import os
import random
import string

import psycopg2


def generate_random_bytes(length=8):
    return os.urandom(length)


def generate_random_name():
    return "".join(random.choices(string.ascii_letters, k=6)).capitalize()


def insert_test_data():
    conn = psycopg2.connect(
        dbname=os.getenv("PG_DB_CKC_POOL"),
        user=os.getenv("PG_DB_USER"),
        password=os.getenv("PG_DB_PASSWORD"),
        host=os.getenv("PG_DB_HOST"),
        port=os.getenv("PG_DB_CKC_POOL_PORT"),
    )
    cur = conn.cursor()

    # Insert into badge
    badge_id = generate_random_bytes(8)
    master_key = generate_random_bytes(8)

    cur.execute(
        """
        INSERT INTO cackalacky.badge (badge_id, master_key)
        VALUES (%s, %s)
        RETURNING id;
    """,
        (badge_id, master_key),
    )

    badge_fk_id = cur.fetchone()[0]

    # Insert into users
    first_name = generate_random_name()
    last_name = generate_random_name()
    discord_handle = f"{first_name.lower()}#{random.randint(1000,9999)}"
    discord_user_id = str(random.randint(100000000000000000, 999999999999999999))

    cur.execute(
        """
        INSERT INTO cackalacky.users (
            first_name,
            last_name,
            discord_handle,
            discord_user_id,
            is_active,
            badge_id
        ) VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
    """,
        (first_name, last_name, discord_handle, discord_user_id, 1, badge_fk_id),  # is_active = True
    )

    user_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    print(f"Inserted badge ID {badge_fk_id} and user ID {user_id}")


if __name__ == "__main__":
    for i in range(1000):
        insert_test_data()
