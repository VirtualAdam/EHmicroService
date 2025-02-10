#docker run --rm --network ehservice_microservices -v "$($PWD.Path):/app" -w /app -e RABBITMQ_HOST=rabbitmq python:3.12-slim bash -c "pip install -r requirements.txt && python -u subscriber_frontdoor_output.py"

import pika
import json
import os
import sys

# Optionally, add the project root to sys.path if you need to import modules from the project.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from config import FRONTDOOR_OUTPUT, declare_all_queues

def callback(ch, method, properties, body):
    message = body.decode()
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        data = message
    print("Received from FRONTDOOR_OUTPUT:", data)

def main():
    # Use the environment variable if set; default to localhost otherwise.
    rabbit_host = os.getenv("RABBITMQ_HOST", "localhost")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host))
    channel = connection.channel()

    # Ensure that all required queues (including FRONTDOOR_OUTPUT) are declared
    declare_all_queues(channel)

    channel.basic_consume(queue=FRONTDOOR_OUTPUT, on_message_callback=callback, auto_ack=True)
    print("Waiting for messages on FRONTDOOR_OUTPUT. Press CTRL+C to exit.")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Exiting...")
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()

