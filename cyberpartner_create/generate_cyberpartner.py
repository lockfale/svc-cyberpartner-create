import json
import logging
import logging.config
import os
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd
import psycopg
import redis
from lockfale_connectors.postgres.pgsql import PostgreSQLConnector

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))

logging.config.fileConfig("log.ini")
logger = logging.getLogger("console")
logger.setLevel(logging.INFO)

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


def apply_stat_multipliers(default_multipliers: Dict[str, Dict], received_stat_modifiers: Dict[str, Dict]) -> Dict[str, Dict]:
    _multipliers = default_multipliers
    for stat_modifier_key in received_stat_modifiers.keys():
        if stat_modifier_key in _multipliers:
            _multipliers.get(stat_modifier_key)["multiplier"] = received_stat_modifiers.get(stat_modifier_key).get("multiplier")

    return _multipliers


def choose_stat_multipliers(attributes: List[Dict]) -> Dict[str, Dict]:
    # Organize attributes by group
    grouped_attributes: Dict[str, List[Dict]] = {}
    for attr in attributes:
        grouped_attributes.setdefault(attr["group"], []).append(attr)

    chosen_multipliers: Dict[str, Dict] = {}

    # Iterate over each group and pick one attribute based on its chance
    for group, attrs in grouped_attributes.items():
        total_chance = sum(attr["chance"] for attr in attrs)
        attrs.append({"name": "default", "chance": (100 - total_chance)})
        chosen_attr = random.choices(population=attrs, weights=[attr["chance"] for attr in attrs], k=1)[0]
        if chosen_attr["name"] != "default":
            chosen_multipliers[group] = chosen_attr

    return chosen_multipliers


def preprocess_weights(items_to_choose: Dict[str, float]) -> Dict[str, float]:
    total_fixed_weight = sum(weight for weight in items_to_choose.values() if weight > 0)
    zero_weight_count = sum(1 for weight in items_to_choose.values() if weight == 0)

    if zero_weight_count > 0:
        remaining_weight = max(0, 100 - total_fixed_weight)  # Ensure it doesn't exceed 100%
        distributed_weight = remaining_weight / zero_weight_count

        # Assign the new weights
        items_to_choose = {item: (distributed_weight if weight == 0 else weight) for item, weight in items_to_choose.items()}

    return items_to_choose


def spin_the_wheel_weighted(items_to_choose: Dict[str, float]) -> str:
    processed_weights = preprocess_weights(items_to_choose)
    chosen_item = random.choices(population=list(processed_weights.keys()), weights=list(processed_weights.values()), k=1)[0]

    return chosen_item


def get_sprite_indexes() -> List[Dict]:
    return [
        {"id": 1, "name": "rock", "index": 0, "weight": 0.1},
        {"id": 2, "name": "pickle", "index": 1, "weight": 0.1},
        {"id": 3, "name": "frankenstein", "index": 2, "weight": 0.1},
        {"id": 4, "name": "kuchitamatchi", "index": 3, "weight": 0},
        {"id": 5, "name": "batabatchi", "index": 4, "weight": 0},
    ]


def get_families() -> List[Dict]:
    return [{"id": 1, "name": "Deeprooted", "weight": 0}, {"id": 2, "name": "Skybound", "weight": 0}]


def get_archetypes() -> List[Dict]:
    return [
        {"id": 1, "name": "Grunt", "weight": 0},
        {"id": 2, "name": "Scout", "weight": 0},
        {"id": 3, "name": "Support", "weight": 0},
        {"id": 4, "name": "Tank", "weight": 0},
    ]


def get_available_attributes() -> List[Dict]:
    return [
        {"id": 1, "group": "age", "name": "ageless", "multiplier": 0, "chance": 1.0},
        {"id": 2, "group": "age", "name": "age_slow", "multiplier": 0.5, "chance": 5.0},
        {"id": 3, "group": "age", "name": "age_fast", "multiplier": 1.5, "chance": 5.0},
        {"id": 4, "group": "hunger", "name": "metabolism_fast", "multiplier": 1.5, "chance": 5.0},
        {"id": 5, "group": "hunger", "name": "metabolism_slow", "multiplier": 0.5, "chance": 5.0},
        {"id": 6, "group": "hunger", "name": "hunger_none", "multiplier": 0, "chance": 1.0},
    ]


def get_default_multipliers() -> Dict[str, Dict]:
    return {
        "age": {"multiplier": 1},
        "hunger": {"multiplier": 1},
        "thirst": {"multiplier": 1},
        "weight": {"multiplier": 1},
        "happiness": {"multiplier": 1},
    }


def get_prefabbed_cyberpartner():
    pass


def get_user_by_badge_id(pgsql: PostgreSQLConnector, badge_id: bytes) -> Optional[pd.DataFrame]:
    CHECK_QRY = """
        select u.id 
        from cackalacky.users u
        JOIN cackalacky.badge b on b.id = u.badge_id 
        where b.badge_id = %(badge_id)s
    """
    params = {"badge_id": psycopg.Binary(badge_id)}
    record = pgsql.select_dict(query=CHECK_QRY, params=params)
    return pd.DataFrame(record)


def get_cyberpartner_by_badge_id(pgsql: PostgreSQLConnector, badge_id: bytes) -> Optional[pd.DataFrame]:
    CHECK_QRY = """
        select cp.id 
        FROM cyberpartner cp
        JOIN cyberpartner_state cps on cps.cyberpartner_id = cp.id
        JOIN users u ON u.id = cp.user_id
        JOIN badge b ON u.badge_id = b.id
        where b.badge_id = %(badge_id)s and cps.status < 1000
    """
    params = {"badge_id": psycopg.Binary(badge_id)}
    record = pgsql.select_dict(query=CHECK_QRY, params=params)
    return pd.DataFrame(record)


def get_cyberpartner_by_badge_id_redis(badge_id: str) -> bool:
    logger.info(f"REDIS get_cyberpartner: {badge_id}")
    redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    snapshot = redis_client.get(badge_id)
    if snapshot:
        return True
    return False


def create_new_cyberpartner(data: Dict) -> Dict:
    """
    0. get user by badge id
    0.1 ensure that user does not have an alive cyberpartner
    1. Determine if prefabbed cp or not
    2. choose the family
    3. set the archetype
    4. choose attributes
    5. generate stats
    :return:
    """
    badge_id = data.get("badge_id")
    if not badge_id:
        logger.error(f"Missing required field(s): badge_id")
        # TODO => otel metric
        return {"error": "Missing required field(s): badge_id"}

    pgsql = PostgreSQLConnector()
    _ref_families = get_families()
    _ref_archetypes = get_archetypes()
    _ref_sprites = get_sprite_indexes()
    _ref_attributes = get_available_attributes()

    family_weights = {family["name"]: family["weight"] for family in _ref_families}
    chosen_family = spin_the_wheel_weighted(family_weights)

    archetypes_weights = {archetype["name"]: archetype["weight"] for archetype in _ref_archetypes}
    chosen_archetype = spin_the_wheel_weighted(archetypes_weights)

    sprite_weights = {sprite["name"]: sprite["weight"] for sprite in _ref_sprites}
    chosen_sprite = spin_the_wheel_weighted(sprite_weights)

    received_attributes = choose_stat_multipliers(_ref_attributes)
    default_multipliers = get_default_multipliers()
    applied_multipliers = apply_stat_multipliers(default_multipliers, received_attributes)

    try:
        user_record = get_user_by_badge_id(pgsql, bytes.fromhex(badge_id))
        if len(user_record) == 0:
            logger.error("User has not registered yet. Cannot create cyberpartner.")
            return {"error": "User has not registered yet. Cannot create cyberpartner."}

        existing_alive_cyberpartner = get_cyberpartner_by_badge_id_redis(badge_id)
        if existing_alive_cyberpartner:
            logger.error(f"Badge {badge_id} already has a cyberpartner... should we kill it?")
            return {"error": f"Badge {badge_id} already has a cyberpartner... should we kill it?"}

        user_record_dict = user_record.to_dict("records")[0]
        cp_stats = {
            "strength": 5,
            "defense": 5,
            "evade": 5,
            "accuracy": 5,
            "speed": 5,
            "vision": 5,
        }
        cp_attributes = [received_attributes[x] for x in received_attributes.keys()]
        now_utc = datetime.now(timezone.utc)
        ts_utc = now_utc.strftime(TIMESTAMP_FORMAT)[:-3]
        cp_obj = {
            "cp": {
                "name": "hello",
                "family": chosen_family,
                "archetype": chosen_archetype,
                "sprite": chosen_sprite,
                "stats": cp_stats,
                "stat_modifiers": applied_multipliers,
                "user_id": user_record_dict["id"],
                "is_active": 1,
            },
            "state": {
                "status": 1,
                "wellness": 1,  # "in good condition," "unresponsive", "sick", "high AF"
                "disposition": 1,
                "life_phase": "Egg",
                "life_phase_change_timestamp": ts_utc,
                "age": 0,
                "hunger": 1555,
                "thirst": 4444,
                "weight": 234,
                "happiness": 100,
                "health": 100,
            },
            "attributes": cp_attributes,
        }

        logger.info(cp_obj)
        return cp_obj
    except Exception as e:
        logger.error(e)
