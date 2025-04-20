import argparse
import json
import random
import time
import uuid

from connectors.kafka_producer import KafkaProducer
from kafka.errors import KafkaError


def create_producer(kafka_broker):
    """Create and return a Kafka producer"""
    return KafkaProducer(kafka_broker=kafka_broker)


def generate_random_badge_id():
    """Generate a random badge ID"""
    return f"badge-{uuid.uuid4().hex[:8]}"


def generate_message(badge_id=None, custom_stats=None):
    """Generate a test message with cyber partner stats"""
    if badge_id is None:
        badge_id = generate_random_badge_id()

    return {"badge_id": badge_id}


def main():
    parser = argparse.ArgumentParser(description="Kafka Cyber Partner Test Producer")
    parser.add_argument("--broker", default="kafka:9092", help="Kafka broker address")
    parser.add_argument("--topic", default="ingress-cackalacky-cyberpartner-create", help="Kafka topic to publish to")
    parser.add_argument("--badge-id", help="Specific badge ID to use (for update mode)")
    args = parser.parse_args()

    producer = create_producer(args.broker)
    print(f"Connected to Kafka broker at {args.broker}")
    payload = {"badge_id": "004ac476"}

    producer.send_message("local-test", args.topic, payload)


if __name__ == "__main__":
    main()
