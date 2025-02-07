import sys
import os
import time
import json
import logging

# Add parent directory so we can import config, auth_utils, etc.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pika
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

import config
from config import (
    DATA_REQUEST,
    DATA_ENTITLEMENT_CHECK,
    DATA_ENTITLEMENT_PASS,
    FRONTDOOR_OUTPUT,  # for sending GET results back
    declare_all_queues
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://myuser:mysecretpassword@postgres:5432/mydb")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class DataRecord(Base):
    __tablename__ = "data_records"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    item_type = Column(String)     # e.g., 'animals' or 'plants'
    table_name = Column(String)    # 'table1' or 'table2'
    payload = Column(Text)         # e.g., name of the item, etc.

Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
channel = None

def on_data_request(ch, method, properties, body):
    """
    Receives messages on the 'data_request' queue.
    We parse the item_type/table, then forward to 'data_entitlement_check'.
    The message should contain a 'method' field like 'POST', 'GET', 'PUT', or 'DELETE'.
    """
    msg_str = body.decode()
    try:
        data = json.loads(msg_str)
    except json.JSONDecodeError:
        logging.error("[DataService] Invalid JSON received on DATA_REQUEST.")
        return

    # e.g., data["method"] = "POST" / "GET" / "PUT" / "DELETE"
    method_name = data.get("method", "GET").upper()
    item_type = data.get("item_type", "unknown").lower()

    if item_type == "animals":
        data["table"] = "table1"
    elif item_type == "plants":
        data["table"] = "table2"
    else:
        logging.error(f"[DataService] Unknown item_type: {item_type}. Not forwarding.")
        return

    # Forward to data_entitlement_check
    ch.basic_publish(
        exchange='',
        routing_key=DATA_ENTITLEMENT_CHECK,
        body=json.dumps(data)
    )
    logging.info(f"[DataService] Received method={method_name}; forwarded to {DATA_ENTITLEMENT_CHECK}")

def on_data_pass(ch, method, properties, body):
    """
    Called when the Entitlement service deems the user is allowed to proceed (DATA_ENTITLEMENT_PASS).
    We read the 'method' field to decide which CRUD action to perform.
    For GET, we publish the result back to FRONTDOOR_OUTPUT.
    """
    msg_str = body.decode()
    try:
        data = json.loads(msg_str)
    except json.JSONDecodeError:
        logging.error("[DataService] Invalid JSON on DATA_ENTITLEMENT_PASS.")
        return

    session = SessionLocal()
    method_name = data.get("method", "GET").upper()
    request_id = data.get("request_id", "N/A")
    item_type = data.get("item_type", "unknown")
    table = data.get("table", None)
    payload = data.get("payload", "")

    logging.info(f"[DataService] [request_id={request_id}] AUTH PASSED => method={method_name}, table={table}")

    try:
        if method_name == "POST":
            # Create/Insert new record
            record = DataRecord(
                request_id=request_id,
                item_type=item_type,
                table_name=table,
                payload=payload
            )
            session.add(record)
            session.commit()
            logging.info(f"[DataService] Inserted new record: {record.payload}")

        elif method_name == "GET":
            # Retrieve matching records
            results = session.query(DataRecord).filter_by(table_name=table).all()
            # Convert to list of dict for JSON
            output = []
            for r in results:
                output.append({
                    "id": r.id,
                    "request_id": r.request_id,
                    "item_type": r.item_type,
                    "table_name": r.table_name,
                    "payload": r.payload
                })

            # Publish results to FRONTDOOR_OUTPUT so the user sees them
            response_msg = {
                "request_id": request_id,
                "method": "GET",
                "results": output
            }
            ch.basic_publish(
                exchange='',
                routing_key=FRONTDOOR_OUTPUT,
                body=json.dumps(response_msg)
            )
            logging.info(f"[DataService] Published GET results to {FRONTDOOR_OUTPUT} => {response_msg}")

        elif method_name == "PUT":
            # For minimal logic: Update first record we find
            record = session.query(DataRecord).filter_by(table_name=table).first()
            if record:
                record.payload = payload
                session.commit()
                logging.info(f"[DataService] Updated record id={record.id}, payload={record.payload}")
            else:
                logging.info("[DataService] No record found to update")

        elif method_name == "DELETE":
            # For minimal logic: Delete the first record we find
            record = session.query(DataRecord).filter_by(table_name=table).first()
            if record:
                session.delete(record)
                session.commit()
                logging.info(f"[DataService] Deleted record id={record.id}")
            else:
                logging.info("[DataService] No record found to delete")

        else:
            logging.info(f"[DataService] Unrecognized method='{method_name}'. No operation performed.")

    except Exception as e:
        logging.error(f"[DataService] DB operation failed: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    # Delay for RabbitMQ startup
    print("[DataService] Waiting 10 seconds before connecting to RabbitMQ...")
    time.sleep(10)
    print(f"[DataService] Using RabbitMQ host: {config.RABBITMQ_HOST}")

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config.RABBITMQ_HOST)
    )
    global channel
    channel = connection.channel()
    declare_all_queues(channel)

    channel.basic_consume(
        queue=DATA_REQUEST,
        on_message_callback=on_data_request,
        auto_ack=True
    )
    channel.basic_consume(
        queue=config.DATA_ENTITLEMENT_PASS,
        on_message_callback=on_data_pass,
        auto_ack=True
    )

    logging.info(f"[DataService] Listening on {DATA_REQUEST} and {config.DATA_ENTITLEMENT_PASS}...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
