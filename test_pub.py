import pika
import json
import uuid
import os

import config
from config import FRONTDOOR, declare_all_queues

def main():
    # Use the RABBITMQ_HOST from the environment, defaulting to localhost if not set.
    host = os.getenv("RABBITMQ_HOST", "localhost")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    channel = connection.channel()

    # Ensure all queues are declared (optional, as microservices may declare them too)
    declare_all_queues(channel)

    test_messages = [
        # 1) Green user (token_app_1) performing a GET on animals
        {
            "request_id": str(uuid.uuid4()),
            "token": "token_app_1",
            "method": "GET",
            "request_type": "data",
            "item_type": "animals",
            "payload": "Fetch details about animals"
        },
        # 2) Blue user (token_app_2) performing a POST on plants (valid for blue)
        {
            "request_id": str(uuid.uuid4()),
            "token": "token_app_2",
            "method": "POST",
            "request_type": "data",
            "item_type": "plants",
            "payload": "Create new plant: rose"
        },
        # 3) Blue user (token_app_2) performing a POST on animals (should be rejected)
        {
            "request_id": str(uuid.uuid4()),
            "token": "token_app_2",
            "method": "POST",
            "request_type": "data",
            "item_type": "animals",
            "payload": "Attempt to create new animal: tiger"
        },
        # 4) Malicious user (token_malicious) performing a PUT on plants (should be rejected)
        {
            "request_id": str(uuid.uuid4()),
            "token": "token_malicious",
            "method": "PUT",
            "request_type": "data",
            "item_type": "plants",
            "payload": "Update plant record: change rose to daisy"
        },
        # 5) Unknown token (results in purple) performing a DELETE on plants (should be rejected)
        {
            "request_id": str(uuid.uuid4()),
            "token": "some_unknown_token",
            "method": "DELETE",
            "request_type": "data",
            "item_type": "plants",
            "payload": "Delete plant record for lily"
        },
        # 6) Green user (token_app_1) performing a DELETE on animals (should pass)
        {
            "request_id": str(uuid.uuid4()),
            "token": "token_app_1",
            "method": "DELETE",
            "request_type": "data",
            "item_type": "animals",
            "payload": "Delete animal record for elephant"
        },
        # 7) Green user with a non-data request (should be processed differently by the controller)
        {
            "request_id": str(uuid.uuid4()),
            "token": "token_app_1",
            "method": "GET",
            "request_type": "other",
            "payload": "Green user requests some non-data info"
        }
    ]

    for msg in test_messages:
        channel.basic_publish(
            exchange='',
            routing_key=FRONTDOOR,
            body=json.dumps(msg)
        )
        print(f"[Publisher] Sent to {FRONTDOOR}: {msg}")

    connection.close()
    print("[Publisher] All test messages sent!")

if __name__ == "__main__":
    main()
