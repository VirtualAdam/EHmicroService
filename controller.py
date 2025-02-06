# controller.py

import pika
import json

import config
from config import (
    FRONTDOOR,
    CONTROLLER_ENTITLEMENT_CHECK,
    CONTROLLER_ENTITLEMENT_PASS,
    DATA_REQUEST,
    declare_all_queues
)

def on_frontdoor_message(ch, method, properties, body):
    """
    1) Receives from frontdoor queue
    2) Forwards to controller_entitlement_check
    """
    message_str = body.decode()
    print(f"[Controller] Received FRONTDOOR: {message_str}")

    try:
        data = json.loads(message_str)
    except json.JSONDecodeError:
        print("[Controller] Invalid JSON => ignore")
        return

    # Publish to entitlement check
    channel.basic_publish(
        exchange='',
        routing_key=CONTROLLER_ENTITLEMENT_CHECK,
        body=json.dumps(data)
    )
    req_id = data.get("request_id", "N/A")
    print(f"[Controller] [request_id={req_id}] => controller_entitlement_check")

def on_controller_pass(ch, method, properties, body):
    """
    1) Receives from controller_entitlement_pass if user is authorized
    2) If request_type == 'data', forward to data_request
    """
    message_str = body.decode()
    data = json.loads(message_str)
    req_id = data.get("request_id", "N/A")

    print(f"[Controller] [request_id={req_id}] PASSED controller entitlement => {message_str}")

    if data.get("request_type") == "data":
        channel.basic_publish(
            exchange='',
            routing_key=DATA_REQUEST,
            body=json.dumps(data)
        )
        print(f"[Controller] [request_id={req_id}] => data_request")
    else:
        print("[Controller] Not a data request => Doing nothing for now.")

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config.RABBITMQ_HOST)
    )
    global channel
    channel = connection.channel()

    declare_all_queues(channel)

    channel.basic_consume(
        queue=FRONTDOOR,
        on_message_callback=on_frontdoor_message,
        auto_ack=True
    )
    channel.basic_consume(
        queue=CONTROLLER_ENTITLEMENT_PASS,
        on_message_callback=on_controller_pass,
        auto_ack=True
    )

    print("[Controller] Listening on FRONTDOOR and CONTROLLER_ENTITLEMENT_PASS...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
