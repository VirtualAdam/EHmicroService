import time
import json
import pika
import config

def publish_message(channel, queue, message):
    """Helper to publish a JSON message to the specified queue."""
    message_json = json.dumps(message)
    channel.basic_publish(exchange='', routing_key=queue, body=message_json)
    print(f"Published to {queue}: {message_json}")

def main():
    # Connect to RabbitMQ using the host from config.
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.RABBITMQ_HOST))
    channel = connection.channel()

    # Declare the FRONTDOOR queue using the same durable setting as declared elsewhere.
    channel.queue_declare(queue=config.FRONTDOOR, durable=False)

    # -----------------------------------------------------------
    # Test 1: Green POST Request (Insert a new record on animals)
    # Expected frontdoor_output response: Success ("Record inserted").
    post_message = {
        "request_id": "1",
        "token": "green",
        "method": "POST",
        "item_type": "animals",
        "payload": "Initial payload for animals"
    }
    publish_message(channel, config.FRONTDOOR, post_message)
    time.sleep(5)

    # -----------------------------------------------------------
    # Test 2: Green PUT Request (Update the existing record on animals)
    # Expected frontdoor_output response: Success ("Record updated").
    put_message = {
        "request_id": "2",
        "token": "green",
        "method": "PUT",
        "item_type": "animals",
        "payload": "Updated payload for animals"
    }
    publish_message(channel, config.FRONTDOOR, put_message)
    time.sleep(5)

    # -----------------------------------------------------------
    # Test 3: Green GET Request (Retrieve records from the animals table)
    # Expected frontdoor_output response: Success with a "results" list including the updated record.
    get_message = {
        "request_id": "3",
        "token": "green",
        "method": "GET",
        "item_type": "animals"
    }
    publish_message(channel, config.FRONTDOOR, get_message)
    time.sleep(5)

    # -----------------------------------------------------------
    # Test 4: Green DELETE Request (Delete the record from the animals table)
    # Expected frontdoor_output response: Success ("Record deleted").
    delete_message = {
        "request_id": "4",
        "token": "green",
        "method": "DELETE",
        "item_type": "animals"
    }
    publish_message(channel, config.FRONTDOOR, delete_message)
    time.sleep(5)

    # -----------------------------------------------------------
    # Additional Test 5: Red Token POST Request to animals (should be rejected)
    red_message = {
        "request_id": "5",
        "token": "red",  # red token is not permitted for animals.
        "method": "POST",
        "item_type": "animals",
        "payload": "Red token test - expected rejection"
    }
    publish_message(channel, config.FRONTDOOR, red_message)
    time.sleep(5)

    # -----------------------------------------------------------
    # Additional Test 6: Purple Token POST Request to animals (should be rejected)
    purple_message = {
        "request_id": "6",
        "token": "purple",  # purple token is not defined in our entitlement rules.
        "method": "POST",
        "item_type": "animals",
        "payload": "Purple token test - expected rejection"
    }
    publish_message(channel, config.FRONTDOOR, purple_message)
    time.sleep(5)

    # -----------------------------------------------------------
    # Additional Test 7: Blue Token GET Request to animals (should be rejected)
    blue_get_animals = {
        "request_id": "7",
        "token": "blue",  # Blue token has no permissions on animals.
        "method": "GET",
        "item_type": "animals"
    }
    publish_message(channel, config.FRONTDOOR, blue_get_animals)
    time.sleep(5)

    # -----------------------------------------------------------
    # Additional Test 8: Blue Token POST Request to plants (should succeed)
    blue_post_plants = {
        "request_id": "8",
        "token": "blue",  # Blue token is allowed to write to plants.
        "method": "POST",
        "item_type": "plants",
        "payload": "Blue token posting to plants - expected success"
    }
    publish_message(channel, config.FRONTDOOR, blue_post_plants)
    time.sleep(5)

    # -----------------------------------------------------------
    # Additional Test 9: Green Token DELETE Request on plants (attempt to delete the plant record posted by blue)
    green_delete_plants = {
        "request_id": "9",
        "token": "green",  # Green token is allowed on plants.
        "method": "DELETE",
        "item_type": "plants",
        "payload": "Green token deleting plant record posted by blue - expected success"
    }
    publish_message(channel, config.FRONTDOOR, green_delete_plants)
    time.sleep(5)

    connection.close()

if __name__ == "__main__":
    main()
