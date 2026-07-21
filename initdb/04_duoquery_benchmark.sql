-- Tabla sintética para experimentos de benchmark

DROP TABLE IF EXISTS actor_big;

CREATE TABLE actor_big AS
SELECT *
FROM actor
CROSS JOIN generate_series(1, 5000);


DROP TABLE IF EXISTS actor_wide;

CREATE TABLE actor_wide AS
SELECT
    actor_id,
    first_name,
    last_name,
    repeat('Lorem ipsum dolor sit amet ', 20) AS bio,
    repeat('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 50) AS notes,
    repeat('yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy', 50) AS comments,
    repeat('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz', 50) AS description
FROM actor
CROSS JOIN generate_series(1, 5000);
