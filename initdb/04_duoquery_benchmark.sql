-- DuoQuery - Estimación energética de consultas SQL
-- Copyright (C) 2026  Eva Molina Jiménez
--
-- Trabajo Fin de Estudios - Grado en Ingeniería Informática
-- Universidad Internacional de La Rioja (UNIR)
--
-- Este archivo forma parte de DuoQuery.
--
-- DuoQuery es software libre: puede redistribuirlo y/o modificarlo
-- bajo los términos de la GNU Affero General Public License publicada
-- por la Free Software Foundation, ya sea la versión 3 de la licencia
-- o (a su elección) cualquier versión posterior.
--
-- DuoQuery se distribuye con la esperanza de que resulte útil, pero
-- SIN NINGUNA GARANTÍA; ni siquiera la garantía implícita de
-- COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulte
-- la GNU Affero General Public License para más detalles.
--
-- Debería haber recibido una copia de la GNU Affero General Public
-- License junto con DuoQuery. Si no, véase <https://www.gnu.org/licenses/>.


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
