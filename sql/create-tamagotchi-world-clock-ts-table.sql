-- create a regular SQL table
CREATE TABLE cackalacky.tamagotchi_world_clock_ts (
  time        TIMESTAMPTZ       NOT NULL,
  day    INT              NOT NULL
);

-- chown
ALTER TABLE cackalacky.tamagotchi_world_clock_ts OWNER TO cackalacky_admin;

-- Then we convert it into a hypertable that is partitioned by time
SELECT create_hypertable('tamagotchi_world_clock_ts', 'time');
