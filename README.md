# DuoQuery

Prototipo funcional, con fines didácticos, para el análisis de consultas SQL y planes de ejecución en PostgreSQL.

## Tecnologías

- PostgreSQL
- Pagila
- Streamlit
- Docker

## Dependencias principales

- streamlit: interfaz web de la aplicación.
- psycopg2-binary: conexión con PostgreSQL.
- pandas: gestión de resultados y tablas.
- sqlparse: validación de que las consultas sean únicamente SELECT.

Las versiones concretas de las dependencias están establecidas en el fichero `requirements.txt`.  
Se incluye también `numpy` y `pyarrow` como dependencias secundarias, fijadas para evitar un problema de compatibilidad detectado entre versiones recientes de estas librerías.

## Ejecución

docker compose up -d --build

Una vez levantados los contenedores, la aplicación queda accesible desde el navegador en `http://localhost:8501`.

## Detener ejecución

docker compose down -v

## Funcionalidades actuales

- Ejecución de consultas SELECT y visualización del resultado.
- Exploración del esquema de la base de datos (tablas, columnas, claves primarias y foráneas).
- Análisis del plan de ejecución (EXPLAIN / EXPLAIN ANALYZE) con avisos explicativos por tipo de nodo.
- Estimación del consumo energético (julios y kWh) y de las emisiones de CO₂e, con selección del país / factor de emisión.
- Indicador de trabajo desperdiciado (filas leídas frente a filas descartadas por los filtros).
- Comparación de dos consultas en paralelo. Dos formas de funcionamiento: modo didáctico (parejas predefinidas) y modo libre.
- Indicador estimado de transferencia de datos (a partir del Plan Width).

## Créditos

**Autor:** Eva Molina Jiménez  
**Trabajo de Fin de Grado (TFG)** - Grado en Ingeniería Informática  
**Universidad Internacional de La Rioja (UNIR)** - 2026  
