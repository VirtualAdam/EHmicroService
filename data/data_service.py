import sys
import os
import time
import json
import logging
import pika
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# Add parent directory to sys.path so shared modules (like config.py) are accessible.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from config import DATA_REQUEST, DATA_ENTITLEMENT_CHECK, DATA_ENTITLEMENT_PASS, FRONTDOOR_OUTPUT, declare_all_queues

# Use environment variable for DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://myuser:mysecretpassword@postgres:5432/mydb")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class DataRecord(Base):
    __tablename__ = "data_records"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    item_type = Column(String)    # e.g., 'animals' or 'plants'
    table_name = Column(String)   # e.g., 'table1' or 'table2'
    payload = Column(Text)

Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)

def publish_message(channel, queue_name, data):
    """Publish and log a message to the specified queue."""
    message_json = json.dumps(data)
    channel.basic_publish(exchange='', routing_key=queue_name, body=message_json)
    logging.info(f"[DataService] Published to '{queue_name}': {message_json}")

def on_data_request(ch, method, properties, body):
    msg_str = body.decode()
    try:
        data = json.loads(msg_str)
    except json.JSONDecodeError:
        logging.error("[DataService] Invalid JSON received on DATA_REQUEST.")
        error_response = {"error": "Invalid JSON", "status": "error"}
        publish_message(ch, FRONTDOOR_OUTPUT, error_response)
        return

    item_type = data.get("item_type", "unknown").lower()
    if item_type == "animals":
        data["table"] = "table1"
    elif item_type == "plants":
        data["table"] = "table2"
    else:
        logging.error(f"[DataService] Unknown item_type: {item_type}. Not forwarding.")
        error_response = {"request_id": data.get("request_id", "N/A"), "status": "error", "message": f"Unknown item_type: {item_type}"}
        publish_message(ch, FRONTDOOR_OUTPUT, error_response)
        return

    # Forward the modified message to DATA_ENTITLEMENT_CHECK.
    publish_message(ch, DATA_ENTITLEMENT_CHECK, data)
    logging.info(f"[DataService] Forwarded to '{DATA_ENTITLEMENT_CHECK}'.")

def on_data_pass(ch, method, properties, body):
    msg_str = body.decode()
    try:
        data = json.loads(msg_str)
    except json.JSONDecodeError:
        logging.error("[DataService] Invalid JSON received on DATA_ENTITLEMENT_PASS.")
        error_response = {"error": "Invalid JSON", "status": "error"}
        publish_message(ch, FRONTDOOR_OUTPUT, error_response)
        return

    request_id = data.get("request_id", "N/A")
    item_type = data.get("item_type", "unknown")
    table = data.get("table")
    method_name = data.get("method", "GET").upper()
    logging.info(f"[DataService] [request_id={request_id}] AUTH PASSED for {item_type} (table: {table}), method: {method_name}. Proceeding with DB operation.")

    session = SessionLocal()
    try:
        if method_name == "POST":
            record = DataRecord(
                request_id=request_id,
                item_type=item_type,
                table_name=table,
                payload=data.get("payload", "")
            )
            session.add(record)
            session.commit()
            logging.info(f"[DataService] [request_id={request_id}] Record inserted.")
            response_msg = {"request_id": request_id, "method": "POST", "status": "success", "message": "Record inserted"}
            publish_message(ch, FRONTDOOR_OUTPUT, response_msg)
        elif method_name == "GET":
            results = session.query(DataRecord).filter_by(table_name=table).all()
            output = [{
                "id": r.id,
                "request_id": r.request_id,
                "item_type": r.item_type,
                "table_name": r.table_name,
                "payload": r.payload
            } for r in results]
            response_msg = {
                "request_id": request_id,
                "method": "GET",
                "status": "success",
                "results": output
            }
            publish_message(ch, FRONTDOOR_OUTPUT, response_msg)
            logging.info(f"[DataService] [request_id={request_id}] Published GET results to '{FRONTDOOR_OUTPUT}'.")
        elif method_name == "PUT":
            record = session.query(DataRecord).filter_by(table_name=table).first()
            if record:
                record.payload = data.get("payload", "")
                session.commit()
                logging.info(f"[DataService] [request_id={request_id}] Record updated.")
                response_msg = {"request_id": request_id, "method": "PUT", "status": "success", "message": "Record updated"}
            else:
                logging.info(f"[DataService] [request_id={request_id}] No record found to update.")
                response_msg = {"request_id": request_id, "method": "PUT", "status": "error", "message": "No record found to update"}
            publish_message(ch, FRONTDOOR_OUTPUT, response_msg)
        elif method_name == "DELETE":
            record = session.query(DataRecord).filter_by(table_name=table).first()
            if record:
                session.delete(record)
                session.commit()
                logging.info(f"[DataService] [request_id={request_id}] Record deleted.")
                response_msg = {"request_id": request_id, "method": "DELETE", "status": "success", "message": "Record deleted"}
            else:
                logging.info(f"[DataService] [request_id={request_id}] No record found to delete.")
                response_msg = {"request_id": request_id, "method": "DELETE", "status": "error", "message": "No record found to delete"}
            publish_message(ch, FRONTDOOR_OUTPUT, response_msg)
        else:
            logging.info(f"[DataService] [request_id={request_id}] Unrecognized method '{method_name}'. No operation performed.")
            response_msg = {"request_id": request_id, "method": method_name, "status": "error", "message": "Unrecognized method"}
            publish_message(ch, FRONTDOOR_OUTPUT, response_msg)
    except Exception as e:
        logging.error(f"[DataService] [request_id={request_id}] DB operation failed: {e}")
        session.rollback()
        error_response = {"request_id": request_id, "method": method_name, "status": "error", "message": f"DB operation failed: {e}"}
        publish_message(ch, FRONTDOOR_OUTPUT, error_response)
    finally:
        session.close()

def main():
    print("[DataService] Waiting 10 seconds before connecting to RabbitMQ...")
    time.sleep(10)
    logging.info(f"[DataService] Connecting to RabbitMQ at '{config.RABBITMQ_HOST}'...")
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.RABBITMQ_HOST))
    global channel
    channel = connection.channel()
    declare_all_queues(channel)

    channel.basic_consume(queue=DATA_REQUEST, on_message_callback=on_data_request, auto_ack=True)
    channel.basic_consume(queue=config.DATA_ENTITLEMENT_PASS, on_message_callback=on_data_pass, auto_ack=True)

    logging.info(f"[DataService] Listening on '{DATA_REQUEST}' and '{config.DATA_ENTITLEMENT_PASS}'...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
