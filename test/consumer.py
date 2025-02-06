import pika

def receive_messages():
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()

    # Declare the same queue
    channel.queue_declare(queue='test_queue')

    # Callback function to handle messages
    def callback(ch, method, properties, body):
        print(f"[x] Received: {body.decode()}")

    # Set up subscription on the queue
    channel.basic_consume(queue='test_queue', on_message_callback=callback, auto_ack=True)
    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    receive_messages()
