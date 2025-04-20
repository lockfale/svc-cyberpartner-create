-- create a regular SQL table
CREATE TABLE cackalacky.tamagotchi_state_ts (
  time        TIMESTAMPTZ       NOT NULL,
  tamagotchi_id    INT              NOT NULL,
  state_change_event TEXT  NULL,
  stat TEXT  NULL,
  stat_value    DOUBLE PRECISION NOT NULL
);

-- chown
ALTER TABLE cackalacky.tamagotchi_state_ts OWNER TO cackalacky_admin;

-- Then we convert it into a hypertable that is partitioned by time
SELECT create_hypertable('tamagotchi_state_ts', 'time');

/** Sample queries

INSERT INTO cackalacky.tamagotchi_state_ts(time, tamagotchi_id, state_change_event, stat, stat_value)
VALUES (NOW(), 2, 'CREATE', 'AGE', 0);

SELECT * FROM cackalacky.tamagotchi_state_ts ORDER BY time DESC LIMIT 100;

SELECT time_bucket('15 minutes', time) AS fifteen_min,
    tamagotchi_id, COUNT(*),
    MAX(STAT_VALUE) AS max_age
  FROM cackalacky.tamagotchi_state_ts
  WHERE time > NOW() - interval '3 hours' AND stat = 'AGE'
  GROUP BY fifteen_min, tamagotchi_id
  ORDER BY fifteen_min DESC, max_age DESC;



 */