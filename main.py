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

redis_db_idx_cp_data = int(os.getenv("REDIS_DB_IDX_CP_DATA", 0))
redis_db_idx_cp_inventory = int(os.getenv("REDIS_DB_IDX_CP_INVENTORY", 5))


def setup_redis():
    """
    Initialize Redis clients for cyberpartner data and inventory.

    Sets up global `REDIS_CLIENT` and `REDIS_CLIENT_INVENTORY` using
    environment variables `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB_IDX_CP_DATA`, and `REDIS_DB_IDX_CP_INVENTORY`.
    """
    global REDIS_CLIENT
    global REDIS_CLIENT_INVENTORY
    REDIS_CLIENT = redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,  # optional, strings not bytes
        db=redis_db_idx_cp_data,
    )
    REDIS_CLIENT_INVENTORY = redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,  # optional, strings not bytes
        db=redis_db_idx_cp_inventory,
    )


def shutdown_redis():
    """
    Gracefully closes the Redis client connections if they are open.
    """
    global REDIS_CLIENT
    global REDIS_CLIENT_INVENTORY
    if REDIS_CLIENT:
        REDIS_CLIENT.close()
    if REDIS_CLIENT_INVENTORY:
        REDIS_CLIENT_INVENTORY.close()


def does_badge_have_cyberpartner(badge_id: str) -> bool:
    """
    Check if a badge has an associated cyberpartner in Redis.

    This function queries the Redis database to determine if a cyberpartner
    exists for the given badge ID. It checks both the main cyberpartner data
    and the inventory data.

    Note: This function does not check the state of the cyberpartner. It only
    checks if a cyberpartner record exists for the badge.


    Parameters
    ----------
    badge_id: str
        The badge ID to check.

    Returns
    -------
    bool
    """
    cp_obj = REDIS_CLIENT.get(badge_id)
    if cp_obj:
        return True
    return False


def upsert_cyberpartner_redis(badge_id: str, cp_obj: Dict):
    """
    Upsert a cyberpartner object in Redis.

    This function updates the cyberpartner data in Redis for the given badge ID.
    It also updates the cyberpartner inventory in Redis.

    Parameters
    ----------
    badge_id: str
    cp_obj: Dict
    """
    REDIS_CLIENT.set(badge_id, json.dumps(cp_obj))
    REDIS_CLIENT_INVENTORY.set(badge_id, json.dumps(create_cp_inventory()))  # fresh inventory


def create_cyberpartner_router(client: KafkaProducer, message: str):
    """
    Route the message to the appropriate handler based on the action type.

    Parameters
    ----------
    client: KafkaProducer
    message: str
    """
    data = json.loads(message) if isinstance(message, str) else message
    if not data.get("badge_id"):
        logger.error(f"Missing required field(s): badge_id")
        return

    action = data.get("action")
    if action:
        cp_data = data.get("cp_obj", {})
        match action:
            case "redis-new":
                return _handle_redis_new(client, data, cp_data)
            case _:
                logger.warning(f"Unhandled action type: {action}")

    existing_cp = does_badge_have_cyberpartner(data.get("badge_id"))
    if existing_cp:
        logger.info(f"Badge {data.get('badge_id')} already has a cyberpartner. Skipping creation.")
        return
    return _handle_new_cyberpartner_creation(client, data)


def _handle_new_cyberpartner_creation(client: KafkaProducer, data: Dict) -> None:
    """
    Handle the creation of a new cyberpartner.

    This function is called when a new cyberpartner needs to be created for a badge.
    It generates the cyberpartner data, sends a message to the Redis handler, and
    sends a success message to the MQTT topic.

    Parameters
    ----------
    client: KafkaProducer
    data: Dict
    """
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
    """
    Handle the creation of a new cyberpartner in Redis.

    Parameters
    ----------
    client: KafkaProducer
    data: Dict
    cp_data: Dict
    """
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
    """
    Main function to run the Kafka consumer and process messages.
    """
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
