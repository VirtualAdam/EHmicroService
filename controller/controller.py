import sys
import os
import time
import json
import logging
import pika

# Add the parent directory so that shared modules (e.g., config.py) can be imported.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from config import FRONTDOOR, CONTROLLER_ENTITLEMENT_CHECK, CONTROLLER_ENTITLEMENT_PASS, DATA_REQUEST, declare_all_queues

logging.basicConfig(level=logging.INFO)

def publish_message(channel, queue_name, data):
    """Publish a message to the specified queue and log the action."""
    message_json = json.dumps(data)
    channel.basic_publish(exchange='', routing_key=queue_name, body=message_json)
    logging.info(f"[Controller] Published to '{queue_name}': {message_json}")

def on_frontdoor_message(ch, method, properties, body):
    """Handles incoming messages from the frontdoor queue and forwards them for entitlement checks."""
    message_str = body.decode()
    logging.info(f"[Controller] Received on '{FRONTDOOR}': {message_str}")
    
    try:
        data = json.loads(message_str)
    except json.JSONDecodeError:
        logging.error("[Controller] Invalid JSON, ignoring message.")
        return

    # Forward to entitlement check
    publish_message(ch, CONTROLLER_ENTITLEMENT_CHECK, data)
    req_id = data.get("request_id", "N/A")
    logging.info(f"[Controller] [request_id={req_id}] Forwarded to '{CONTROLLER_ENTITLEMENT_CHECK}'.")

def on_controller_pass(ch, method, properties, body):
    """Handles messages from entitlement_pass and determines if they should be forwarded to data_request."""
    message_str = body.decode()
    
    try:
        data = json.loads(message_str)
    except json.JSONDecodeError:
        logging.error("[Controller] Invalid JSON in pass message.")
        return

    req_id = data.get("request_id", "N/A")
    logging.info(f"[Controller] [request_id={req_id}] Received from '{CONTROLLER_ENTITLEMENT_PASS}': {message_str}")

    # Forward all POST, PUT, GET, DELETE requests to the data service
    if data.get("method") in ["POST", "PUT", "GET", "DELETE"]:
        publish_message(ch, DATA_REQUEST, data)
        logging.info(f"[Controller] [request_id={req_id}] Forwarded to '{DATA_REQUEST}'.")
    else:
        logging.info(f"[Controller] [request_id={req_id}] Not a valid data request; no further action.")

def main():
    """Main function to set up RabbitMQ connection and start consuming messages."""
    logging.info("[Controller] Waiting 10 seconds before connecting to RabbitMQ...")
    time.sleep(10)
    logging.info(f"[Controller] Connecting to RabbitMQ at '{config.RABBITMQ_HOST}'...")
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.RABBITMQ_HOST))
    channel = connection.channel()
    declare_all_queues(channel)

    channel.basic_consume(queue=FRONTDOOR, on_message_callback=on_frontdoor_message, auto_ack=True)
    channel.basic_consume(queue=CONTROLLER_ENTITLEMENT_PASS, on_message_callback=on_controller_pass, auto_ack=True)

    logging.info("[Controller] Waiting for messages on 'FRONTDOOR' and 'CONTROLLER_ENTITLEMENT_PASS'...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
