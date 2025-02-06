import pika, json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='authenticated')

# Pretend we passed RBAC
passed_message = {
    "sender": "user123",
    "payload": "some request info",
    "request_type": "data"
}
channel.basic_publish(exchange='', routing_key='authenticated', body=json.dumps(passed_message))
print("[Test] Simulated RBAC pass -> 'authenticated'.")
connection.close()
