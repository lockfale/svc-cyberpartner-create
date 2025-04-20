import argparse

#!/usr/bin/env python3
import json

from kafka import KafkaConsumer


def create_consumer(kafka_broker, topic, group_id=None):
    """Create and return a Kafka consumer"""
    return KafkaConsumer(
        topic,
        bootstrap_servers=kafka_broker,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id=group_id,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )


def display_cyber_partner(message):
    """Display cyber partner information in a nicely formatted way"""
    try:
        if isinstance(message, str):
            data = json.loads(message)
        else:
            data = message

        badge_id = data.get("badge_id", "Unknown")
        cp_stats = data.get("cp_stats", {})

        print(f"\n===== Cyber Partner: {badge_id} =====")

        if cp_stats:
            # Just dump the stats directly
            print("Stats:")
            for key, value in cp_stats.items():
                print(f"  {key}: {value}")
        else:
            print("No stats available")

    except Exception as e:
        print(f"Error displaying message: {str(e)}")
        print(f"Raw message: {message}")


def main():
    parser = argparse.ArgumentParser(description="Kafka Cyber Partner Test Consumer")
    parser.add_argument("--broker", default="kafka:9092", help="Kafka broker address")
    parser.add_argument("--topic", default="flink-egress-state-update", help="Kafka topic to consume from")
    parser.add_argument("--group", default="test-consumer-group", help="Consumer group ID")
    args = parser.parse_args()

    print(f"Connecting to Kafka broker at {args.broker}")
    print(f"Consuming messages from topic: {args.topic}")
    print("Waiting for messages... (Press Ctrl+C to exit)")

    consumer = create_consumer(args.broker, args.topic, args.group)

    try:
        for message in consumer:
            print("\n" + "=" * 50)
            print(f"Received message from partition {message.partition}, offset {message.offset}")
            display_cyber_partner(message.value)
    except KeyboardInterrupt:
        print("\nExiting consumer")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
