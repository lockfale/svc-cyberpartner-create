import argparse
import copy
import json
import logging
import logging.config
import os
from datetime import datetime, timezone
from typing import Dict, Optional

import redis
from lockfale_connectors.lf_kafka.kafka_consumer import KafkaConsumer
from lockfale_connectors.lf_kafka.kafka_producer import KafkaProducer

from cyberpartner_create import generate_cyberpartner
from cyberpartner_create.generate_cyberpartner import create_cp_inventory

logging.config.fileConfig("log.ini")
logger = logging.getLogger("console")
logger.setLevel(logging.INFO)

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
REDIS_CLIENT: Optional[redis.Redis] = None
REDIS_CLIENT_INVENTORY: Optional[redis.Redis] = None

redis_db_idx_cp_inventory = int(os.getenv("REDIS_DB_IDX_CP_INVENTORY", 5))

def setup_redis():
    global REDIS_CLIENT
    global REDIS_CLIENT_INVENTORY
    REDIS_CLIENT = redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,  # optional, strings not bytes
        db=0,
    )
    REDIS_CLIENT_INVENTORY = redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,  # optional, strings not bytes
        db=redis_db_idx_cp_inventory,
    )


def shutdown_redis():
    global REDIS_CLIENT
    global REDIS_CLIENT_INVENTORY
    if REDIS_CLIENT:
        REDIS_CLIENT.close()
    if REDIS_CLIENT_INVENTORY:
        REDIS_CLIENT_INVENTORY.close()



def upsert_cyberpartner_redis(badge_id: str, cp_obj: Dict):
    logger.info(f"REDIS insert_cyberpartner: {cp_obj.get('cp', {}).get('id')}")
    REDIS_CLIENT.set(badge_id, json.dumps(cp_obj))
    REDIS_CLIENT_INVENTORY.set(badge_id, json.dumps(create_cp_inventory()))  # fresh inventory


def create_cyberpartner_router(client: KafkaProducer, message: str):
    """forcing build."""
    data = json.loads(message) if isinstance(message, str) else message

    # Handle badge_id creation flow
    if data.get("badge_id") and not data.get("action"):
        return _handle_new_cyberpartner_creation(client, data)

    # Handle action-based flows
    action = data.get("action")
    if action:
        cp_data = data.get("cp_obj", {})
        match action:
            case "redis-new":
                return _handle_redis_new(client, data, cp_data)
            case _:
                logger.warning(f"Unhandled action type: {action}")


def _handle_new_cyberpartner_creation(client: KafkaProducer, data: Dict) -> None:
    new_cp_obj = generate_cyberpartner.create_new_cyberpartner(data)
    data["action"] = "redis-new"
    data["cp_obj"] = new_cp_obj

    topic = "ingress-cackalacky-cyberpartner-create"
    if new_cp_obj.get("error"):
        topic = "egress-mqtt-to-badge"
        data["result"] = 0
        del data["cp_obj"]
        del data["action"]

    client.send_message(source_topic="ingress-cackalacky-cyberpartner-create", destination_topic=topic, message=data)


def _handle_redis_new(client: KafkaProducer, data: Dict, cp_data: Dict) -> None:
    if not cp_data.get("state"):
        logger.error("REDIS => missing state key")
        return

    upsert_cyberpartner_redis(data.get("badge_id"), cp_data)

    # Send success message
    client.send_message(
        source_topic="ingress-cackalacky-cyberpartner-create",
        destination_topic="egress-mqtt-to-badge",
        message={"result": 1, **data},
    )

    # Trigger reporting base action
    base_payload = copy.deepcopy(data)
    base_payload.update({"action": "reporting-base", "result": 1})
    client.send_message(
        source_topic="ingress-cackalacky-cyberpartner-create", destination_topic="cyberpartner-create-additional", message=base_payload
    )
    try:
        base_payload["new_state"] = base_payload["cp_obj"]
        now_utc = datetime.now(timezone.utc)
        ts_utc = now_utc.strftime(TIMESTAMP_FORMAT)[:-3]
        base_payload["message_received_ts"] = ts_utc
        client.send_message(source_topic="ingress-cackalacky-cyberpartner-create", destination_topic="cyberpartner-event-log", message=base_payload)
    except Exception as e:
        logger.error(f"Error registering create event: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Kafka Cyber Partner Test Consumer")
    parser.add_argument("--topic", default="flink-egress-state-update", help="Kafka topic to consume from")
    parser.add_argument("--group", default="test-consumer-group", help="Consumer group ID")
    args = parser.parse_args()

    logger.info(f"Connecting to Kafka broker at {os.getenv('KAFKA_BROKERS_SVC')}")
    logger.info(f"Consuming messages from topic: {args.topic}")
    logger.info(f"Group ID: {args.group}")

    try:
        consumer = KafkaConsumer(os.getenv("KAFKA_BROKERS_SVC"), [args.topic], args.group)
        setup_redis()
        producer_client = KafkaProducer(kafka_broker=os.getenv("KAFKA_BROKERS_SVC"))
    except Exception as e:
        logger.error(f"Error initializing resources: {str(e)}")
        return

    logger.info("Waiting for messages... (Press Ctrl+C to exit)")
    try:
        for message in consumer.consumer:
            create_cyberpartner_router(producer_client, message.value)
    except KeyboardInterrupt:
        logger.info("\nExiting consumer.")
    finally:
        consumer.disconnect()
        producer_client.disconnect()
        shutdown_redis()


if __name__ == "__main__":
    main()
