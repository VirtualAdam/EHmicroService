# entitlement_service.py

import pika
import json

import config
from config import (
    CONTROLLER_ENTITLEMENT_CHECK,
    CONTROLLER_ENTITLEMENT_PASS,
    DATA_ENTITLEMENT_CHECK,
    DATA_ENTITLEMENT_PASS,
    REJECTED,
    declare_all_queues
)
from auth_utils import decode_token, can_access_table

def handle_entitlement_request(ch, method, properties, body, pass_queue):
    """
    Common logic for "controller_entitlement_check" or "data_entitlement_check".
    """
    message_str = body.decode()

    try:
        message_data = json.loads(message_str)
    except json.JSONDecodeError:
        print("[Entitlement] Invalid JSON => rejected")
        forward_message(ch, REJECTED, {"error": "Invalid JSON"})
        return

    token = message_data.get("token", "")
    role = decode_token(token)

    # If this request is for 'data_entitlement_check', we might have a 'table' field
    # We'll verify the user can access that table if present:
    if pass_queue == config.DATA_ENTITLEMENT_PASS:
        table = message_data.get("table")  # e.g., "table1" or "table2"
        if not table:
            # If no table specified, we treat as invalid
            print("[Entitlement] Missing 'table' => rejected")
            forward_message(ch, REJECTED, message_data)
            return

        # If role can access this table => pass, else => reject
        if can_access_table(role, table):
            forward_message(ch, pass_queue, message_data)
            print(f"[Entitlement] role={role} => data_entitlement_pass (table={table})")
        else:
            forward_message(ch, REJECTED, message_data)
            print(f"[Entitlement] role={role}, table={table} => rejected (no access)")
    else:
        # The controller flow (controller_entitlement_check)
        # 'green' or 'blue' => pass; 'red' or 'purple' => reject
        if role in ["green", "blue"]:
            forward_message(ch, pass_queue, message_data)
            print(f"[Entitlement] role={role} => {pass_queue}")
        else:
            forward_message(ch, REJECTED, message_data)
            print(f"[Entitlement] role={role} => rejected")

def on_controller_check(ch, method, properties, body):
    handle_entitlement_request(ch, method, properties, body, config.CONTROLLER_ENTITLEMENT_PASS)

def on_data_check(ch, method, properties, body):
    handle_entitlement_request(ch, method, properties, body, config.DATA_ENTITLEMENT_PASS)

def forward_message(channel, queue_name, data):
    channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(data))

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config.RABBITMQ_HOST)
    )
    channel = connection.channel()

    # Declare all queues
    declare_all_queues(channel)

    # Listen for controller checks
    channel.basic_consume(
        queue=config.CONTROLLER_ENTITLEMENT_CHECK,
        on_message_callback=on_controller_check,
        auto_ack=True
    )

    # Listen for data checks
    channel.basic_consume(
        queue=config.DATA_ENTITLEMENT_CHECK,
        on_message_callback=on_data_check,
        auto_ack=True
    )

    print("[Entitlement] Waiting on *entitlement_check queues...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
