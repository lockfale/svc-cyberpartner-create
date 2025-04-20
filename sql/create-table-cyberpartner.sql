-- DROP TABLE IF EXISTS cackalacky.cyberpartner;
CREATE TABLE IF NOT EXISTS cackalacky.cyberpartner
(
    id serial PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    family VARCHAR(255) NOT NULL,
    archetype VARCHAR(255) NOT NULL,
    sprite VARCHAR(255) NOT NULL,
    stats JSONB NOT NULL,
    stat_modifier JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active SMALLINT NOT NULL
);

ALTER TABLE cackalacky.cyberpartner
ADD COLUMN user_id INT,
ADD CONSTRAINT fk_cyberpartner_user FOREIGN KEY (user_id) REFERENCES cackalacky.users(id) ON DELETE SET NULL;


CREATE TRIGGER trigger_set_updated_at_cyberpartner
BEFORE UPDATE ON cackalacky.cyberpartner
FOR EACH ROW
EXECUTE FUNCTION cackalacky.set_updated_at();

ALTER TABLE cackalacky.cyberpartner OWNER TO cackalacky_admin;