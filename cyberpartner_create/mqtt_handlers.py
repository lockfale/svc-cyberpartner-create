import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

from lockfale_connectors.lf_kafka.kafka_producer import KafkaProducer
from paho.mqtt.client import MQTTMessage

logger = logging.getLogger("console")

# Static topic routes
TOPIC_ROUTE_MAPPING = {
    "default": lambda topic, payload: logger.info(f"Message: {payload.decode('utf-8')}"),
}

executor = ThreadPoolExecutor(max_workers=4)


def send_to_kafka(source_topic: str, destination_topic: str, message: Dict = None):
    badge_id = source_topic.split("/")[3]

    if not badge_id:
        logger.error(f"Missing required field(s): badge_id")
        # TODO => otel metric
        return

    if not message:
        message = {}

    client = KafkaProducer(kafka_broker=os.getenv("KAFKA_BROKERS_SVC"))
    message["badge_id"] = badge_id
    client.send_message(source_topic=source_topic, destination_topic=destination_topic, key=badge_id, message=message)
    client.disconnect()


# Wildcard topic routes
WILDCARD_TOPICS = [(re.compile(r"^cackalacky/badge/egress/[^/]+/cyberpartner/create$"), send_to_kafka)]


def matching_topic_handler(topic):
    """Finds a matching function for the given topic"""
    if topic in TOPIC_ROUTE_MAPPING:
        return TOPIC_ROUTE_MAPPING[topic]

    for pattern, handler in WILDCARD_TOPICS:
        if pattern.match(topic):
            return handler

    return TOPIC_ROUTE_MAPPING["default"]


def on_connect(client, userdata, flags, reason_code, properties):
    """Handles MQTT connection"""
    logger.info(f"Connected with result code: {reason_code}")

    if reason_code.is_failure:
        logger.error(f"Failed to connect: {reason_code}")
        return

    subscription_list = [
        ("cackalacky/badge/egress/+/cyberpartner/create", 1),
    ]
    logger.info(f"Subscribing to:")
    logger.info(subscription_list)
    client.subscribe(subscription_list)


def on_message(client, userdata, message: MQTTMessage):
    """Handles incoming MQTT messages"""
    if message.retain:
        logger.info("Skipping retained message")
        return

    data = json.loads(message.payload.decode("utf-8"))
    handler = matching_topic_handler(message.topic)
    executor.submit(handler, message.topic, "ingress-cackalacky-cyberpartner-create", data)
