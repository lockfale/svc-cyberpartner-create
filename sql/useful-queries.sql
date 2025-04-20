/* View badge ids */
select encode(badge_id, 'hex') from badge;

/* Get Cyberpartner by badge */
select *
FROM cyberpartner cp
JOIN cyberpartner_state cps on cps.cyberpartner_id = cp.id
JOIN users u ON u.id = cp.user_id
JOIN badge b ON u.badge_id = b.id
WHERE b.badge_id = decode('004ac476', 'hex');

/* Reset CP tables */
DELETE FROM cackalacky.cyberpartner_state where cyberpartner_id > 256;
DELETE FROM cackalacky.cyberpartner_attributes where cyberpartner_id > 256;
DELETE FROM cackalacky.cyberpartner where id > 256;