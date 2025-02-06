# test_frontdoor_publisher.py

import pika
import json
import uuid

import config
from config import FRONTDOOR, declare_all_queues

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config.RABBITMQ_HOST)
    )
    channel = connection.channel()

    # Ensure all queues are declared
    declare_all_queues(channel)

    test_messages = [
        # 1) A "green" user token, data request about animals
        {
           #"request_id": str(uuid.uuid4()),
            "request_id": "001",
            "token": "token_app_1",
            "request_type": "data",
            "item_type": "animals",
            "payload": "Green user wants info about animals"
        },
        # 2) A "blue" user token, data request about animals
        {
            #"request_id": str(uuid.uuid4()),
            "request_id": "002",
            "token": "token_app_2",
            "request_type": "data",
            "item_type": "animals",
            "payload": "Blue user wants info about animals"
        },
        # 3) A "blue" user token, data request about plants (valid for blue => table2)
        {
            #"request_id": str(uuid.uuid4()),
            "request_id": "003",
            "token": "token_app_2",
            "request_type": "data",
            "item_type": "plants",
            "payload": "Blue user wants info about plants"
        },
        # 4) Malicious token => red => always rejected
        {
            #"request_id": str(uuid.uuid4()),
            "request_id": "004",
            "token": "token_malicious",
            "request_type": "data",
            "item_type": "animals",
            "payload": "Malicious attempt"
        },
        # 5) Unknown token => purple => also rejected
        {
            #"request_id": str(uuid.uuid4()),
            "request_id": "005",
            "token": "some_unknown_token",
            "request_type": "data",
            "item_type": "plants",
            "payload": "Unknown token attempt"
        },
        # 6) Green user with a non-data request
        {
            #"request_id": str(uuid.uuid4()),
            "request_id": "006",
            "token": "token_app_1",
            "request_type": "other",
            "payload": "Green user requests something else"
        }
    ]

    for msg in test_messages:
        channel.basic_publish(
            exchange='',
            routing_key=FRONTDOOR,
            body=json.dumps(msg)
        )
        print(f"[Publisher] Sent to frontdoor: {msg}")

    connection.close()
    print("[Publisher] All test messages sent!")

if __name__ == "__main__":
    main()
