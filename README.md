# DuoQuery

Herramienta didáctica para el análisis de consultas SQL y planes de ejecución en PostgreSQL.

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

Las versiones concretas de las dependencias están establecidas en el fichero `requirements.txt`. Se incluye también `numpy` y `pyarrow` como dependencias secundarias, fijadas para evitar un problema de compatibilidad detectado entre versiones recientes de estas librerías.

## Ejecución

docker compose up -d --build

## Detener ejecución

docker compose down -v

## Funcionalidades actuales

- Ejecución de consultas SELECT
- Exploración del esquema
- Análisis de planes EXPLAIN
- Estadísticas básicas de ejecución

## Créditos

**Autor:** Eva Molina Jiménez  
**Trabajo de Fin de Grado (TFG)** - Grado en Ingeniería Informática  
**Universidad Internacional de La Rioja (UNIR)** - 2026  
