import json
import logging
import logging.config
import os
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import ntplib

from lockfale_connectors.mqtt.mqtt_publisher import MQTTPublisher

"""Force"""
logging.config.fileConfig("log.ini")
logger = logging.getLogger("console")
logger.setLevel(logging.INFO)

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))

def get_ntp_time(server="pool.ntp.org"):
    client = ntplib.NTPClient()
    response = client.request(server, version=3)
    return datetime.fromtimestamp(response.tx_time, tz=ZoneInfo("Europe/Vienna"))


def new_cp_redis():
    return f"badge-{uuid.uuid4().hex[:8]}"


def create_cp(_pub: MQTTPublisher, badge_id):
    _topic = f"cackalacky/badge/egress/{badge_id}/cp/create"
    ntp_dt = get_ntp_time()
    epoch_ts = ntp_dt.timestamp()
    json_obj = {"ts": epoch_ts}
    logger.info(json_obj)
    msg_info = _pub.publish(
        _topic,
        json.dumps(json_obj),
    )
    msg_info.wait_for_publish()


if __name__ == "__main__":
    logger.info(f'Starting up create CP | {os.getenv("DOPPLER_ENVIRONMENT")}')
    mqtt_host = os.getenv("MQTT_HOST")
    mqtt_port = int(os.getenv("MQTT_PORT"))
    if mqtt_host is None or mqtt_port is None:
        logger.error("MQTT_HOST or MQTT_PORT is not set")
        exit(1)

    import uuid

    random_str = str(uuid.uuid4()).split("-")[0]

    dplr_env = os.getenv("DOPPLER_ENVIRONMENT")
    mqtt_pub = MQTTPublisher(f"publisher-local-create-cp-{random_str}")
    mqtt_pub.connect(keep_alive=360)
    mqtt_pub.client.loop_start()
    import json
    import random

    import redis

    ids = ["004ac476"]  # no CP yet
    for badge_id in ids:
        create_cp(mqtt_pub, badge_id)
