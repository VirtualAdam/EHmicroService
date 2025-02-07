import sys
import os
import time  # import time for sleep

# Ensure the parent directory is in the Python path so that config.py can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import pika
import config
from config import FRONTDOOR, CONTROLLER_ENTITLEMENT_CHECK, CONTROLLER_ENTITLEMENT_PASS, DATA_REQUEST, declare_all_queues

def on_frontdoor_message(ch, method, properties, body):
    message_str = body.decode()
    print(f"[Controller] Received on FRONTDOOR: {message_str}")
    try:
        data = json.loads(message_str)
    except json.JSONDecodeError:
        print("[Controller] Invalid JSON => ignoring")
        return

    # Forward the message to the controller entitlement check queue
    ch.basic_publish(
        exchange='',
        routing_key=CONTROLLER_ENTITLEMENT_CHECK,
        body=json.dumps(data)
    )
    req_id = data.get("request_id", "N/A")
    print(f"[Controller] [request_id={req_id}] => forwarded to {CONTROLLER_ENTITLEMENT_CHECK}")

def on_controller_pass(ch, method, properties, body):
    message_str = body.decode()
    data = json.loads(message_str)
    req_id = data.get("request_id", "N/A")
    print(f"[Controller] [request_id={req_id}] Passed controller entitlement: {message_str}")

    if data.get("request_type") == "data":
        # Forward data requests to the data_request queue for further processing
        ch.basic_publish(
            exchange='',
            routing_key=DATA_REQUEST,
            body=json.dumps(data)
        )
        print(f"[Controller] [request_id={req_id}] => forwarded to {DATA_REQUEST}")
    else:
        print(f"[Controller] [request_id={req_id}] Not a data request; no further action.")

def main():
    # Add a delay to give RabbitMQ time to start up (e.g., 10 seconds)
    print("[Controller] Waiting 10 seconds before connecting to RabbitMQ...")
    time.sleep(10)

    print(f"[Controller] Using RabbitMQ host: {config.RABBITMQ_HOST}")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.RABBITMQ_HOST))
    channel = connection.channel()
    declare_all_queues(channel)

    channel.basic_consume(queue=FRONTDOOR, on_message_callback=on_frontdoor_message, auto_ack=True)
    channel.basic_consume(queue=CONTROLLER_ENTITLEMENT_PASS, on_message_callback=on_controller_pass, auto_ack=True)

    print("[Controller] Waiting for messages on FRONTDOOR and CONTROLLER_ENTITLEMENT_PASS...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
