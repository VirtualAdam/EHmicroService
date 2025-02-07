import sys
import os
import time  # Import time to allow for a startup delay

# Add parent directory to the Python path so shared modules (like config.py) can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import logging
import pika
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

import config
from config import DATA_REQUEST, DATA_ENTITLEMENT_CHECK, DATA_ENTITLEMENT_PASS, declare_all_queues

# Use the DATABASE_URL from the environment, with a default value
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://myuser:mysecretpassword@postgres:5432/mydb")

# --- SQLAlchemy Setup ---
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class DataRecord(Base):
    __tablename__ = "data_records"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    item_type = Column(String)    # 'animals' or 'plants'
    table_name = Column(String)   # 'table1' or 'table2'
    payload = Column(Text)

# Create the tables if they don't exist
Base.metadata.create_all(bind=engine)

def on_data_request(ch, method, properties, body):
    msg_str = body.decode()
    try:
        data = json.loads(msg_str)
    except json.JSONDecodeError:
        logging.error("[DataService] Invalid JSON received on DATA_REQUEST.")
        return

    item_type = data.get("item_type", "unknown").lower()
    if item_type == "animals":
        data["table"] = "table1"
    elif item_type == "plants":
        data["table"] = "table2"
    else:
        logging.error(f"[DataService] Unknown item_type: {item_type}.")
        return

    # Forward the modified message to DATA_ENTITLEMENT_CHECK
    ch.basic_publish(
        exchange='',
        routing_key=DATA_ENTITLEMENT_CHECK,
        body=json.dumps(data)
    )
    logging.info(f"[DataService] Forwarded to {DATA_ENTITLEMENT_CHECK}: {data}")

def on_data_pass(ch, method, properties, body):
    msg_str = body.decode()
    try:
        data = json.loads(msg_str)
    except json.JSONDecodeError:
        logging.error("[DataService] Invalid JSON received on DATA_ENTITLEMENT_PASS.")
        return

    request_id = data.get("request_id")
    item_type = data.get("item_type")
    table = data.get("table")
    logging.info(f"[DataService] [request_id={request_id}] AUTH PASSED for {item_type} (table: {table}). Proceeding with DB operation.")

    session = SessionLocal()
    try:
        record = DataRecord(
            request_id=request_id,
            item_type=item_type,
            table_name=table,
            payload=data.get("payload", "")
        )
        session.add(record)
        session.commit()
        logging.info(f"[DataService] [request_id={request_id}] Inserted record into database.")
    except Exception as e:
        logging.error(f"[DataService] DB operation failed: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    logging.basicConfig(level=logging.INFO)

    # Add a delay before connecting to RabbitMQ
    print("[DataService] Waiting 10 seconds before connecting to RabbitMQ...")
    time.sleep(10)
    print(f"[DataService] Using RabbitMQ host: {config.RABBITMQ_HOST}")

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.RABBITMQ_HOST))
    global channel
    channel = connection.channel()
    declare_all_queues(channel)

    channel.basic_consume(queue=DATA_REQUEST, on_message_callback=on_data_request, auto_ack=True)
    channel.basic_consume(queue=config.DATA_ENTITLEMENT_PASS, on_message_callback=on_data_pass, auto_ack=True)

    logging.info(f"[DataService] Listening on {DATA_REQUEST} and {config.DATA_ENTITLEMENT_PASS}...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
