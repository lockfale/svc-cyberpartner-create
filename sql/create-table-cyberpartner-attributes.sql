-- DROP TABLE IF EXISTS cackalacky.cyberpartner_attributes;
CREATE TABLE IF NOT EXISTS cackalacky.cyberpartner_attributes
(
    id serial PRIMARY KEY,
    cyberpartner_id INT NOT NULL,
    attribute_json JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active SMALLINT NOT NULL DEFAULT 1
);

CREATE TRIGGER trigger_set_updated_at_cyberpartner_attributes
BEFORE UPDATE ON cackalacky.cyberpartner_attributes
FOR EACH ROW
EXECUTE FUNCTION cackalacky.set_updated_at();

ALTER TABLE cackalacky.cyberpartner_attributes OWNER TO cackalacky_admin;