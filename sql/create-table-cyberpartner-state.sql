-- DROP TABLE IF EXISTS cackalacky.cyberpartner_state;
CREATE TABLE IF NOT EXISTS cackalacky.cyberpartner_state
(
    id serial PRIMARY KEY,
    cyberpartner_id INT NOT NULL,
    status INT NOT NULL,
    wellness INT NOT NULL,
    disposition INT NOT NULL,
    age INT NOT NULL,
    hunger INT NOT NULL,
    thirst INT NOT NULL,
    weight INT NOT NULL,
    happiness INT NOT NULL,
    health INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER trigger_set_updated_at_cyberpartner_state
BEFORE UPDATE ON cackalacky.cyberpartner_state
FOR EACH ROW
EXECUTE FUNCTION cackalacky.set_updated_at();

ALTER TABLE cackalacky.cyberpartner_state OWNER TO cackalacky_admin;