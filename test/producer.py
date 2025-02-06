import pika
import json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='frontdoor')

message_data = {
    "sender": "user123",
    "payload": "some request info"
}
channel.basic_publish(
    exchange='',
    routing_key='frontdoor',
    body=json.dumps(message_data)
)
print("[Producer] Sent to 'frontdoor'.")
connection.close()
