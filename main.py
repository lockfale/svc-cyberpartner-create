import argparse
import copy
import json
import logging
import logging.config
import os
from typing import Dict
from datetime import datetime, timezone

from lockfale_connectors.lf_kafka.kafka_consumer import KafkaConsumer
from lockfale_connectors.lf_kafka.kafka_producer import KafkaProducer
from lockfale_connectors.postgres.pgsql import PostgreSQLConnector

from cyberpartner_create import generate_cyberpartner, insert_cyberpartner

logging.config.fileConfig("log.ini")
logger = logging.getLogger("console")
logger.setLevel(logging.INFO)

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


def create_cyberpartner_router(message: str):
    """forcing build"""
    data = json.loads(message) if isinstance(message, str) else message

    # Handle badge_id creation flow
    if data.get("badge_id") and not data.get("action"):
        return _handle_new_cyberpartner_creation(data)

    # Handle action-based flows
    action = data.get("action")
    if action:
        cp_data = data.get("cp_obj", {})
        match action:
            case "reporting-base":
                return _handle_reporting_base(data, cp_data)
            case "redis-new":
                return _handle_redis_new(data, cp_data)
            case "redis-update-id":
                return _handle_redis_update_id(data, cp_data)
            case "reporting-state":
                return _handle_reporting_state(data, cp_data)
            case "reporting-attributes":
                return _handle_reporting_attributes(data, cp_data)
            case _:
                logger.warning("Unhandled action type")

    # default case
    display_cyber_partner(data)


def _handle_new_cyberpartner_creation(data: Dict) -> None:
    new_cp_obj = generate_cyberpartner.create_new_cyberpartner(data)
    data["action"] = "redis-new"
    data["cp_obj"] = new_cp_obj
    logger.info(data)

    topic = "ingress-cackalacky-cyberpartner-create"
    if new_cp_obj.get("error"):
        topic = "egress-mqtt-to-badge"
        data["result"] = 0
        del data["cp_obj"]
        del data["action"]

    client = KafkaProducer(kafka_broker=os.getenv("KAFKA_BROKERS_SVC"))
    client.send_message(source_topic="ingress-cackalacky-cyberpartner-create", destination_topic=topic, key=data.get("badge_id"), message=data)
    client.disconnect()


def _handle_reporting_base(data: Dict, cp_data: Dict) -> None:
    enriched_obj = copy.deepcopy(cp_data)
    base_payload = copy.deepcopy(data)
    del base_payload["action"]

    pgsql = PostgreSQLConnector()
    enriched_obj["cp"] = insert_cyberpartner.insert_cyberpartner(pgsql, cp_data)

    client = KafkaProducer(kafka_broker=os.getenv("KAFKA_BROKERS_SVC"))
    base_payload["cp_obj"] = enriched_obj

    messages = [
        {"action": "redis-update-id", **base_payload},
        {"action": "reporting-state", **base_payload},
        {"action": "reporting-attributes", **base_payload},
    ]

    for msg in messages:
        client.send_message(
            source_topic="ingress-cackalacky-cyberpartner-create",
            destination_topic="ingress-cackalacky-cyberpartner-create",
            key=data.get("badge_id"),
            message=msg,
        )
    client.disconnect()


def _handle_redis_new(data: Dict, cp_data: Dict) -> None:
    if not cp_data.get("state"):
        logger.error("REDIS => missing state key")
        return

    insert_cyberpartner.upsert_cyberpartner_redis(data.get("badge_id"), cp_data)
    client = KafkaProducer(kafka_broker=os.getenv("KAFKA_BROKERS_SVC"))

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
        source_topic="ingress-cackalacky-cyberpartner-create", destination_topic="ingress-cackalacky-cyberpartner-create", message=base_payload
    )
    try:
        base_payload['new_state'] = base_payload['cp_obj']
        now_utc = datetime.now(timezone.utc)
        ts_utc = now_utc.strftime(TIMESTAMP_FORMAT)[:-3]
        base_payload["message_received_ts"] = ts_utc
        client.send_message(
            source_topic="ingress-cackalacky-cyberpartner-create",
            destination_topic="cyberpartner-event-log", message=base_payload
        )
    except Exception as e:
        logger.error(f"Error registering create event: {str(e)}")


def _handle_redis_update_id(data: Dict, cp_data: Dict) -> None:
    """Forcing build"""
    current_state = insert_cyberpartner.get_cyberpartner_redis(data.get("badge_id"))
    if current_state.get("cp", {}).get("id"):
        logger.error("CURRENT STATE => already has id key")
        return

    cp_id = cp_data.get("cp", {}).get("id", -1)
    if cp_id == -1:
        logger.error("MESSAGE STATE => missing id key")
        return

    prev_state = copy.deepcopy(current_state)
    try:
        current_state["cp"]["id"] = cp_id
        insert_cyberpartner.upsert_cyberpartner_redis(data.get("badge_id"), current_state)
        payload = {**data, "cp_obj": current_state}
    except Exception as e:
        logger.error(f"Error updating Redis: {str(e)}")
        return

    try:
        payload.update({'new_state': current_state, 'prev_state': prev_state})
        now_utc = datetime.now(timezone.utc)
        ts_utc = now_utc.strftime(TIMESTAMP_FORMAT)[:-3]
        payload["message_received_ts"] = ts_utc
        client = KafkaProducer(kafka_broker=os.getenv("KAFKA_BROKERS_SVC"))
        client.send_message(
            source_topic="ingress-cackalacky-cyberpartner-create",
            destination_topic="cyberpartner-event-log", message=payload
        )
    except Exception as e:
        logger.error(f"Error registering create event: {str(e)}")


def _handle_reporting_state(data: Dict, cp_data: Dict) -> None:
    if not data.get("cp_obj", {}).get("state"):
        logger.error("STATE => missing state key")
        return

    pgsql = PostgreSQLConnector()
    insert_cyberpartner.insert_cyberpartner_state(pgsql, cp_data)


def _handle_reporting_attributes(data: Dict, cp_data: Dict) -> None:
    if not data.get("cp_obj", {}).get("attributes", []):
        logger.error("ATTRIBUTES => missing attributes key")
        return

    pgsql = PostgreSQLConnector()
    insert_cyberpartner.insert_cyberpartner_attributes(pgsql, cp_data)


def display_cyber_partner(data: Dict):
    """Display cyber partner information in a nicely formatted way"""
    try:
        logger.info(f"\n===== DEFAULT =====")
        logger.info(data)
    except Exception as e:
        logger.info(f"Error displaying message: {str(e)}")
        logger.info(f"Raw message: {data}")


TOPIC_MAP = {
    "ingress-cackalacky-cyberpartner-create": create_cyberpartner_router,
    "default": display_cyber_partner,
}


def main():
    parser = argparse.ArgumentParser(description="Kafka Cyber Partner Test Consumer")
    parser.add_argument("--topic", default="flink-egress-state-update", help="Kafka topic to consume from")
    parser.add_argument("--group", default="test-consumer-group", help="Consumer group ID")
    args = parser.parse_args()

    logger.info(f"Connecting to Kafka broker at {os.getenv('KAFKA_BROKERS_SVC')}")
    logger.info(f"Consuming messages from topic: {args.topic}")
    logger.info(f"Group ID: {args.group}")
    logger.info("Waiting for messages... (Press Ctrl+C to exit)")

    consumer = KafkaConsumer(os.getenv("KAFKA_BROKERS_SVC"), [args.topic], args.group)

    try:
        for message in consumer.consumer:
            TOPIC_MAP.get(args.topic, TOPIC_MAP.get("default"))(message.value)
    except KeyboardInterrupt:
        logger.info("\nExiting consumer")
    finally:
        consumer.disconnect()


if __name__ == "__main__":
    main()
