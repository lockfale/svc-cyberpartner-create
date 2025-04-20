import json
import logging
import logging.config
import os
from typing import Dict

import redis
from lockfale_connectors.postgres.pgsql import PostgreSQLConnector

logging.config.fileConfig("log.ini")
logger = logging.getLogger("console")
logger.setLevel(logging.INFO)

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))


def insert_cyberpartner(pgsql: PostgreSQLConnector, cp_obj: Dict) -> Dict:
    logger.info(f"Inserting new cyberpartner: {cp_obj.get("cp").get('name')}")
    INSERT_QRY = """
            INSERT INTO cackalacky.cyberpartner (name, family, archetype, sprite, user_id, stats, stat_modifier, is_active) 
            VALUES (%(name)s, %(family)s, %(archetype)s,  %(sprite)s,  %(user_id)s, %(stats)s, %(stat_modifier)s, 1) RETURNING id
        """
    params = {
        "name": cp_obj.get("cp").get("name"),
        "family": cp_obj.get("cp").get("family"),
        "archetype": cp_obj.get("cp").get("archetype"),
        "sprite": cp_obj.get("cp").get("sprite"),
        "user_id": cp_obj.get("cp").get("user_id"),
        "stats": json.dumps(cp_obj.get("cp").get("stats")),
        "stat_modifier": json.dumps(cp_obj.get("cp").get("stat_modifiers")),
    }
    record_id = pgsql.execute(query=INSERT_QRY, params=params)
    cp_obj["cp"]["id"] = record_id
    return cp_obj["cp"]


def insert_cyberpartner_state(pgsql: PostgreSQLConnector, cp_obj: Dict) -> int:
    logger.info(f"insert_cyberpartner_state: {cp_obj.get("cp").get('id')}")
    INSERT_QRY = """
            INSERT INTO cackalacky.cyberpartner_state (cyberpartner_id, status, life_phase, wellness, disposition, age, hunger, thirst, weight, happiness, health) 
            VALUES (%(cyberpartner_id)s, %(status)s, %(life_phase)s, %(wellness)s,  %(disposition)s,  %(age)s,  %(hunger)s,  %(thirst)s,  %(weight)s,  %(happiness)s,  %(health)s) RETURNING id
        """
    params = {
        "cyberpartner_id": cp_obj.get("cp").get("id"),
        "status": cp_obj.get("state").get("status"),
        "life_phase": cp_obj.get("state").get("life_phase"),
        "wellness": cp_obj.get("state").get("wellness"),
        "disposition": cp_obj.get("state").get("disposition"),
        "age": cp_obj.get("state").get("age"),
        "hunger": cp_obj.get("state").get("hunger"),
        "thirst": cp_obj.get("state").get("thirst"),
        "weight": cp_obj.get("state").get("weight"),
        "happiness": cp_obj.get("state").get("happiness"),
        "health": cp_obj.get("state").get("health"),
    }
    record_id = pgsql.execute(query=INSERT_QRY, params=params)
    return record_id


def get_cyberpartner_redis(badge_id: str) -> Dict:
    logger.info(f"REDIS get_cyberpartner: {badge_id}")
    redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    cp_obj = redis_client.get(badge_id)
    if cp_obj:
        return json.loads(cp_obj)
    return {}


def upsert_cyberpartner_redis(badge_id: str, cp_obj: Dict):
    logger.info(f"REDIS insert_cyberpartner: {cp_obj.get('cp', {}).get('id')}")
    redis_client = redis.Redis(host=redis_host, port=redis_port)
    redis_client.set(badge_id, json.dumps(cp_obj))


def insert_cyberpartner_attributes(pgsql: PostgreSQLConnector, cp_obj: Dict):
    logger.info(f"insert_cyberpartner_attributes: {cp_obj.get('cp').get('id')} | {len(cp_obj.get('attributes'))} attributes")
    values_array = []
    params = {}
    for idx, _ in enumerate(cp_obj.get("attributes")):
        params[f"cyberpartner_id_{idx}"] = cp_obj.get("cp").get("id")
        params[f"attribute_json_{idx}"] = json.dumps(cp_obj.get("attributes")[idx])
        values_array.append(f"(%(cyberpartner_id_{idx})s, %(attribute_json_{idx})s)")

    values_string = ",\n".join(values_array)
    INSERT_QRY = f"""
            INSERT INTO cackalacky.cyberpartner_attributes (cyberpartner_id, attribute_json) 
            VALUES {values_string};
        """
    _ = pgsql.execute(query=INSERT_QRY, params=params)
