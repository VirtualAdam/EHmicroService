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
                    DATA_ENTITLEMENT_CHECK, DATA_ENTITLEMENT_PASS, REJECTED, FRONTDOOR_OUTPUT, declare_all_queues)

logging.basicConfig(level=logging.INFO)

# Load entitlement rules from the JSON file once at startup.
current_dir = os.path.dirname(os.path.abspath(__file__))
rules_path = os.path.join(current_dir, "entitlement_rules.json")
try:
    with open(rules_path, "r") as f:
        RULES = json.load(f)
    logging.info(f"[Entitlement] Loaded entitlement rules from '{rules_path}'.")
except Exception as e:
    logging.error(f"[Entitlement] Failed to load entitlement rules: {e}")
    RULES = {}

def publish_message(channel, queue_name, data):
    """Publish and log a message to the specified queue."""
    message_json = json.dumps(data)
    channel.basic_publish(exchange='', routing_key=queue_name, body=message_json)
    logging.info(f"[Entitlement] Published to '{queue_name}': {message_json}")

def handle_entitlement_request(ch, method, properties, body, pass_queue):
    message_str = body.decode()
    try:
        message_data = json.loads(message_str)
    except json.JSONDecodeError:
        logging.error("[Entitlement] Invalid JSON; rejecting message.")
        error_response = {"error": "Invalid JSON", "status": "error"}
        publish_message(ch, REJECTED, error_response)
        publish_message(ch, FRONTDOOR_OUTPUT, error_response)
        return

    # Instead of using auth_utils, treat the token as the role directly.
    role = message_data.get("token", "").lower()  # Expect token to be a role, e.g., "green", "blue", "red"
    method_name = message_data.get("method", "GET").upper()
    item_type = message_data.get("item_type", "unknown").lower()

    # Map HTTP method to action: GET => read, others (POST, PUT, DELETE) => write.
    action = "read" if method_name == "GET" else "write"
    
    # Retrieve the allowed actions for the role and item_type from the entitlement rules.
    allowed_actions = RULES.get(role, {}).get(item_type, [])
    allowed = action in allowed_actions

    if allowed:
        publish_message(ch, pass_queue, message_data)
        logging.info(f"[Entitlement] [role={role}, item={item_type}, method={method_name}] => PASSED to '{pass_queue}'.")
    else:
        # Prepare a rejection message and publish to both REJECTED and FRONTDOOR_OUTPUT queues.
        rejection_msg = message_data.copy()
        rejection_msg.update({"status": "rejected", "reason": "Unauthorized request"})
        publish_message(ch, REJECTED, rejection_msg)
        publish_message(ch, FRONTDOOR_OUTPUT, rejection_msg)
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
