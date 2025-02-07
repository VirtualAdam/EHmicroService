import sys
import os
import time
import json
import logging
import pika

# Ensure the parent directory is on the Python path.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from config import (CONTROLLER_ENTITLEMENT_CHECK, CONTROLLER_ENTITLEMENT_PASS,
                    DATA_ENTITLEMENT_CHECK, DATA_ENTITLEMENT_PASS, REJECTED, declare_all_queues)
from auth_utils import decode_token

logging.basicConfig(level=logging.INFO)

def publish_message(channel, queue_name, data):
    """Publish and log message to specified queue."""
    message_json = json.dumps(data)
    channel.basic_publish(exchange='', routing_key=queue_name, body=message_json)
    logging.info(f"[Entitlement] Published to '{queue_name}': {message_json}")

def handle_entitlement_request(ch, method, properties, body, pass_queue):
    message_str = body.decode()
    try:
        message_data = json.loads(message_str)
    except json.JSONDecodeError:
        logging.error("[Entitlement] Invalid JSON; rejecting message.")
        publish_message(ch, REJECTED, {"error": "Invalid JSON"})
        return

    token = message_data.get("token", "")
    role = decode_token(token)  # e.g., "green", "blue", "red", or "purple"
    method_name = message_data.get("method", "GET").upper()
    item_type = message_data.get("item_type", "unknown").lower()

    # For simplicity, here is a basic check:
    # - Green users: allow all
    # - Blue users: allow only if item_type is "plants"
    # - Red and Purple: reject
    allowed = False
    if role == "green":
        allowed = True
    elif role == "blue":
        allowed = (item_type == "plants")
    
    if allowed:
        publish_message(ch, pass_queue, message_data)
        logging.info(f"[Entitlement] [role={role}, item={item_type}, method={method_name}] => PASSED to '{pass_queue}'.")
    else:
        publish_message(ch, REJECTED, message_data)
        logging.info(f"[Entitlement] [role={role}, item={item_type}, method={method_name}] => REJECTED.")

def on_controller_check(ch, method, properties, body):
    handle_entitlement_request(ch, method, properties, body, CONTROLLER_ENTITLEMENT_PASS)

def on_data_check(ch, method, properties, body):
    handle_entitlement_request(ch, method, properties, body, DATA_ENTITLEMENT_PASS)

def main():
    logging.info("[Entitlement] Waiting 10 seconds before connecting to RabbitMQ...")
    time.sleep(10)
    logging.info(f"[Entitlement] Connecting to RabbitMQ at '{config.RABBITMQ_HOST}'...")
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.RABBITMQ_HOST))
    channel = connection.channel()
    declare_all_queues(channel)

    channel.basic_consume(queue=CONTROLLER_ENTITLEMENT_CHECK, on_message_callback=on_controller_check, auto_ack=True)
    channel.basic_consume(queue=DATA_ENTITLEMENT_CHECK, on_message_callback=on_data_check, auto_ack=True)

    logging.info(f"[Entitlement] Listening on '{CONTROLLER_ENTITLEMENT_CHECK}' and '{DATA_ENTITLEMENT_CHECK}'...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
