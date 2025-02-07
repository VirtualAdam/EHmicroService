import sys
import os
import time
import json

# Add the parent directory so we can import config, auth_utils, etc.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pika

import config
from config import (
    CONTROLLER_ENTITLEMENT_CHECK,
    CONTROLLER_ENTITLEMENT_PASS,
    DATA_ENTITLEMENT_CHECK,
    DATA_ENTITLEMENT_PASS,
    REJECTED,
    FRONTDOOR_OUTPUT,  # in case we need future expansions
    declare_all_queues
)
from auth_utils import decode_token

# === Load the JSON rules once at startup ===
RULES_FILE = os.path.join(os.path.dirname(__file__), "entitlement_rules.json")

def load_rules():
    with open(RULES_FILE, "r") as f:
        return json.load(f)

ENTITLEMENT_RULES = load_rules()
# Example structure:
# {
#   "green": {"animals": ["read", "write"], "plants": ["read", "write"]},
#   "blue":  {"animals": [],               "plants": ["read", "write"]},
#   "red":   {"animals": [],               "plants": []}
# }

def can_access(role, item_type, method):
    """
    role: 'green', 'blue', 'red', or unknown (-> 'purple')
    item_type: 'animals' or 'plants'
    method: 'GET', 'POST', 'PUT', 'DELETE'
    => returns True if allowed, otherwise False
    """

    # If role isn't recognized (e.g. purple), no access
    if role not in ENTITLEMENT_RULES:
        return False

    # If item_type doesn't exist for the role, no access
    if item_type not in ENTITLEMENT_RULES[role]:
        return False

    # Determine if this is a read or write request
    # - GET => "read"
    # - POST, PUT, DELETE => "write"
    if method.upper() == "GET":
        needed_perm = "read"
    else:
        needed_perm = "write"

    # Check if the needed_perm is in the array from the JSON
    return needed_perm in ENTITLEMENT_RULES[role][item_type]

def forward_message(channel, queue_name, data):
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(data)
    )

def handle_entitlement_request(ch, method, properties, body, pass_queue):
    """
    Common logic for both controller_entitlement_check and data_entitlement_check.
    If user is entitled, forward to pass_queue (controller/data).
    Otherwise, forward to REJECTED.
    """
    message_str = body.decode()
    try:
        message_data = json.loads(message_str)
    except json.JSONDecodeError:
        print("[Entitlement] Invalid JSON => rejected")
        forward_message(ch, REJECTED, {"error": "Invalid JSON"})
        return

    token = message_data.get("token", "")
    role = decode_token(token)  # "green", "blue", "red", or "purple"
    method_name = message_data.get("method", "GET").upper()
    item_type = message_data.get("item_type", "unknown")

    if can_access(role, item_type, method_name):
        forward_message(ch, pass_queue, message_data)
        print(f"[Entitlement] role={role}, item={item_type}, method={method_name} => PASS => {pass_queue}")
    else:
        forward_message(ch, REJECTED, message_data)
        print(f"[Entitlement] role={role}, item={item_type}, method={method_name} => REJECTED")

def on_controller_check(ch, method, properties, body):
    handle_entitlement_request(ch, method, properties, body, config.CONTROLLER_ENTITLEMENT_PASS)

def on_data_check(ch, method, properties, body):
    handle_entitlement_request(ch, method, properties, body, config.DATA_ENTITLEMENT_PASS)

def main():
    # Delay to ensure RabbitMQ is ready
    print("[Entitlement] Waiting 10 seconds before connecting to RabbitMQ...")
    time.sleep(10)
    print(f"[Entitlement] Using RabbitMQ host: {config.RABBITMQ_HOST}")

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config.RABBITMQ_HOST)
    )
    channel = connection.channel()

    # Declare queues
    declare_all_queues(channel)

    channel.basic_consume(
        queue=CONTROLLER_ENTITLEMENT_CHECK,
        on_message_callback=on_controller_check,
        auto_ack=True
    )
    channel.basic_consume(
        queue=DATA_ENTITLEMENT_CHECK,
        on_message_callback=on_data_check,
        auto_ack=True
    )

    print(f"[Entitlement] Listening for messages on {CONTROLLER_ENTITLEMENT_CHECK} and {DATA_ENTITLEMENT_CHECK}...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
