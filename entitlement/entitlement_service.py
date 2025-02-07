import sys
import os
import time  # For startup delay

# Add the parent directory to sys.path so that shared modules are accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import pika

import config
from config import CONTROLLER_ENTITLEMENT_CHECK, CONTROLLER_ENTITLEMENT_PASS, DATA_ENTITLEMENT_CHECK, DATA_ENTITLEMENT_PASS, REJECTED, declare_all_queues
from auth_utils import decode_token, can_access_table

def handle_entitlement_request(ch, method, properties, body, pass_queue):
    message_str = body.decode()
    try:
        message_data = json.loads(message_str)
    except json.JSONDecodeError:
        print("[Entitlement] Invalid JSON => rejected")
        forward_message(ch, REJECTED, {"error": "Invalid JSON"})
        return

    token = message_data.get("token", "")
    role = decode_token(token)

    if pass_queue == config.DATA_ENTITLEMENT_PASS:
        table = message_data.get("table")
        if not table:
            print("[Entitlement] Missing 'table' => rejected")
            forward_message(ch, REJECTED, message_data)
            return
        if can_access_table(role, table):
            forward_message(ch, pass_queue, message_data)
            print(f"[Entitlement] role={role} => {pass_queue} (table={table})")
        else:
            forward_message(ch, REJECTED, message_data)
            print(f"[Entitlement] role={role}, table={table} => rejected (no access)")
    else:
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
    # Delay before connecting to RabbitMQ
    print("[Entitlement] Waiting 10 seconds before connecting to RabbitMQ...")
    time.sleep(10)
    print(f"[Entitlement] Using RabbitMQ host: {config.RABBITMQ_HOST}")

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.RABBITMQ_HOST))
    channel = connection.channel()
    declare_all_queues(channel)

    channel.basic_consume(queue=CONTROLLER_ENTITLEMENT_CHECK, on_message_callback=on_controller_check, auto_ack=True)
    channel.basic_consume(queue=DATA_ENTITLEMENT_CHECK, on_message_callback=on_data_check, auto_ack=True)

    print(f"[Entitlement] Waiting for messages on {CONTROLLER_ENTITLEMENT_CHECK} and {DATA_ENTITLEMENT_CHECK}...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
