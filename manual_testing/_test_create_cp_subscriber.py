import logging
import logging.config
import os
import time

from lockfale_connectors.mqtt.mqtt_subscriber import MQTTSubscriber

logging.config.fileConfig("log.ini")
logger = logging.getLogger("console")
logger.setLevel(logging.INFO)

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))


def on_connect(client, userdata, flags, reason_code, properties):
    """Handles MQTT connection"""
    logger.info(f"Connected with result code: {reason_code}")

    if reason_code.is_failure:
        logger.error(f"Failed to connect: {reason_code}")
        return

    # simulate being the badge
    subscription_list = [
        ("cackalacky/badge/ingress/004ac476/cyberpartner/create", 1),
    ]
    logger.info(f"Subscribing to:")
    logger.info(subscription_list)
    client.subscribe(subscription_list)


def on_message(client, userdata, message):
    """Handles incoming MQTT messages"""
    if message.retain:
        logger.info("Skipping retained message")
        return

    logger.info(message.topic)
    logger.info(message.payload)


if __name__ == "__main__":
    logger.info(f'Starting up create CP subscriber | {os.getenv("DOPPLER_ENVIRONMENT")}')
    mqtt_host = os.getenv("MQTT_HOST")
    mqtt_port = int(os.getenv("MQTT_PORT"))
    if mqtt_host is None or mqtt_port is None:
        logger.error("MQTT_HOST or MQTT_PORT is not set")
        exit(1)

    import uuid

    random_str = str(uuid.uuid4()).split("-")[0]
    dplr_env = os.getenv("DOPPLER_ENVIRONMENT")

    badge_id = "004ac476"
    mqtt_subscriber = MQTTSubscriber(f"subscriber-local-create-cp-{random_str}", _on_connect=on_connect, _on_message=on_message)
    mqtt_subscriber.connect(keep_alive=360)

    counter = 0
    mqtt_subscriber.start_listener()
    while True:
        time.sleep(0.1)
        counter += 1
        if counter % 1000 == 0:
            logger.info(f"Heartbeat: {counter}")
            counter = 0
