# data_service.py

import pika
import json

import config
from config import (
    DATA_REQUEST,
    DATA_ENTITLEMENT_CHECK,
    DATA_ENTITLEMENT_PASS,
    declare_all_queues
)

def on_data_request(ch, method, properties, body):
    """
    Incoming data requests on 'data_request'.
    We parse whether it's 'animals' or 'plants'.
    Then set table=table1 or table2 accordingly.
    Finally, we ask the Entitlement service to confirm user can access that table.
    """
    msg_str = body.decode()
    try:
        data = json.loads(msg_str)
    except json.JSONDecodeError:
        print("[DataService] Invalid JSON => ignoring")
        return

    item_type = data.get("item_type", "unknown").lower()
    # Decide table1 for animals, table2 for plants
    if item_type == "animals":
        data["table"] = "table1"
    elif item_type == "plants":
        data["table"] = "table2"
    else:
        # If we don't recognize the item_type, let's reject or handle differently
        print(f"[DataService] Unknown item_type={item_type} => cannot proceed.")
        return

    # Publish to data_entitlement_check
    channel.basic_publish(
        exchange='',
        routing_key=DATA_ENTITLEMENT_CHECK,
        body=json.dumps(data)
    )
    print(f"[DataService] Forwarded to data_entitlement_check => {data}")

def on_data_pass(ch, method, properties, body):
    """
    Called when Entitlement returns an approved message on 'data_entitlement_pass'.
    We finalize the CRUD action here (fake logic).
    """
    msg_str = body.decode()
    data = json.loads(msg_str)

    request_id = data.get("request_id")
    item_type = data.get("item_type")
    table = data.get("table")

    print(f"[DataService] [request_id={request_id}] AUTH PASSED for {item_type} => {table}")
    # Here you'd do real DB operations. We'll just log success:
    print(f"[DataService] (DB ACTION) User can access {table} for {item_type}. Operation complete.")

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config.RABBITMQ_HOST)
    )
    global channel
    channel = connection.channel()

    declare_all_queues(channel)

    # 1) Listen for raw data requests
    channel.basic_consume(
        queue=DATA_REQUEST,
        on_message_callback=on_data_request,
        auto_ack=True
    )

    # 2) Listen for successful entitlements
    channel.basic_consume(
        queue=DATA_ENTITLEMENT_PASS,
        on_message_callback=on_data_pass,
        auto_ack=True
    )

    print("[DataService] Listening on data_request and data_entitlement_pass...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
