import logging
import logging.config
import os
from typing import Dict

from lockfale_connectors.lf_kafka.kafka_producer import KafkaProducer

logging.config.fileConfig("log.ini")
logger = logging.getLogger("console")
logger.setLevel(logging.INFO)


def send_to_kafka(source_topic: str, destination_topic: str, message: Dict = None):
    badge_id = source_topic.split("/")[3]

    if not badge_id:
        logger.error(f"Missing required field(s): badge_id")
        # TODO => otel metric
        return

    client = KafkaProducer(kafka_broker=os.getenv("KAFKA_BROKERS_SVC"))
    msg = {"badge_id": badge_id}
    client.send_message(source_topic=source_topic, destination_topic=destination_topic, key=badge_id, message=msg)
    client.disconnect()
