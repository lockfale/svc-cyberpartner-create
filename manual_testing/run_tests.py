import logging
import logging.config
import os
import time

from lockfale_connectors.mqtt.mqtt_publisher import MQTTPublisher

logging.config.fileConfig("log.ini")
logger = logging.getLogger("console")
logger.setLevel(logging.INFO)

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))


def new_cp_redis():
    return f"badge-{uuid.uuid4().hex[:8]}"


def update_cp_world_event(_pub: MQTTPublisher):
    _topic = "cackalacky/world/event/day/1"
    msg_info = _pub.publish(
        _topic,
        "",
    )
    msg_info.wait_for_publish()


def create_cp(_pub: MQTTPublisher, badge_id):
    _topic = f"cackalacky/badge/egress/{badge_id}/cyberpartner/create"
    msg_info = _pub.publish(
        _topic,
        '{"requester": "nutcrunch"}',
    )
    msg_info.wait_for_publish()


def kill_cp(_pub: MQTTPublisher):
    _topic = f"cackalacky/badge/egress/004AC476/cyberpartner/death"
    msg_info = _pub.publish(
        _topic,
        "{}",
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

    # update_cp_world_event(mqtt_pub)

    ids = [
        "a6aff7faf0cbf307",
        "d8248f78e231d022",
        "2a9bca82e7e6c23d",
        "155234dcec82e046",
        "8aa58546ea5f3f42",
        "dace4533b6c49f9b",
        "62ec15006b220fdc",
        "7f50947a875ab19c",
        "d793c27f5e1e35c1",
        "e3691f30324fcec1",
        "b90b4c6c11fbb124",
        "af05b0ff08c05aa5",
        "bfb944d588e61123",
        "3ae92fef20971bc8",
        "1cd1b4e7563f8238",
        "db0b86c7e08b0ed5",
        "16c6fba9e1bf3f98",
        "79cf2cf9e5a27e0d",
        "c9e00b706264b3d2",
        "b780c7dfd7874f30",
        "99b5a07161bd4c5d",
        "bca4c94caa0f04a4",
        "5efc3aed5b90a9da",
        "d336862cdf7f0cad",
        "c4deb8a9f1cfeb6f",
        "4c127e0a44bf3c5a",
        "7252732fffc9935d",
        "2283062d6d9d123c",
        "1a26b066e83b491d",
        "49c2e00623ddd503",
        "2ec40082c9d7d4ae",
        "c9b967005497d095",
        "f1ef861750122665",
        "2693eef4bf03354b",
        "280486613195361d",
        "31efe8da04143c11",
        "acfde7081aa8432d",
        "ba409c09015f1480",
        "3a90481cbbe78bfc",
        "dbea393e1f8ac95c",
        "14713360e5efa01b",
        "021466a8b33f9a1d",
        "6f9f3a4293ac8df3",
        "611464c87bf2aca2",
        "2c876f852bbc8369",
        "7b7b51ae6f0ca079",
        "a1b318ae7ceb4a72",
        "d446e8febde4bfa9",
        "355f1bed3cef4e2d",
        "3cb3795feea7f580",
        "6ebbcbf310c03c98",
        "a302dc04fbeb4771",
        "7a85d28746b4c5f9",
        "b46713b674d32d75",
        "0626196f51919dcc",
        "824ca83182ecfdba",
        "9cd9d5680a73b205",
        "22ca36f462162189",
        "4ea291b7c281ae77",
        "533d370646cd0228",
        "d06d38e499ff2714",
        "a8c00c70ac5482f3",
        "d67f9c6dea76a6f3",
        "e16cde5beacf9868",
        "4440b4d0abcc928b",
        "942bc7975fe3e37e",
        "84c647dc3f1309b9",
        "ae84449097d984fb",
        "2790d46bee6e9a09",
        "2b051be063ec973e",
        "519a412db34f6620",
        "b06a713ee2bf980c",
        "660f7f0c4b4df622",
        "923973b1c85f97b6",
        "afca8be02b4659b7",
        "a2ddbc62274903b5",
        "9c39b0262e769eee",
        "6bffffdf2ff66052",
        "1f319182f0fdb2df",
        "a3f0debeedbdae0a",
        "2123c26e6b7f507b",
        "6e5e742a6113e118",
        "650fcfe992f220f3",
        "7e4be84e1b202ec0",
        "fb7682e64fa9fa27",
        "6890c1443f580a80",
        "c277a1f6a060f799",
        "56ad0c92fefb4776",
        "eaddbad9621301ac",
        "ed62f52d951e2bfa",
        "088b261dae8a9207",
        "71bc2a69c78fdcd2",
        "34bcfafa9728c0fc",
        "9da71e8fef92d3e5",
        "7f3f3d277700b5b6",
        "e1691ff5ad36cc8d",
        "5320b197d7f2df86",
        "a8818418866c76ec",
        "4c62b16ed66174a1",
        "4a9099634cf6eb1a",
        "b22d8ad9dd0dc325",
        "2a0abb965a00f754",
        "f9bcb33c137eb966",
        "b3628fe0939a7b98",
        "7e1ee19396f3452e",
        "1064fe821f7bf965",
        "5923751cdd66cff7",
        "dd480e71024ca427",
        "d42dfbb7ccaafdfe",
        "cb3c98def2861cee",
        "8743f286fff1eb5d",
        "824df7882418db85",
        "39feeabbfd93a879",
        "1d462fa898590f62",
        "2767132e619d30b6",
        "58e7e57df6d0d9a3",
    ]
    for badge_id in ids:
        create_cp(mqtt_pub, badge_id)
    # for i in range(1000):
    #     b_id = new_cp_redis()
    #     redis_client = redis.Redis(host="localhost", port=redis_port, decode_responses=True)
    #
    #     cp_state_obj = {}
    #
    #     redis_client.set(b_id, json.dumps(cp_state_obj))

    # while True:
    #     # Determine a random number of times to call the function (3 to 30)
    #     num_calls = random.randint(5, 15)
    #
    #     print(f"Spawning {num_calls} cps...")
    #
    #     # Execute the function the random number of times
    #     for _ in range(num_calls):
    #         create_cp(mqtt_pub)
    #
    #     # Wait for 60 seconds before repeating
    #     rand_sleep = random.randint(2, 6)
    #     sleep_secs = rand_sleep * 30
    #     print(f"Waiting for {sleep_secs} seconds before next batch...")
    #     time.sleep(sleep_secs)
