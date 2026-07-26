"""
benchmark_queries.py

Colección oficial de consultas de validación de DuoQuery.

Estas consultas se utilizan para:

- Validar el modelo energético.
- Generar resultados reproducibles.
- Alimentar la futura pestaña de consultas didácticas.
- Generar tablas y gráficos para la memoria.
"""

BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "group": "projection",
        "title": "Seleccionar todas las columnas",
        "objective": "Evaluar el impacto de recuperar todas las columnas.",
        "sql": """
            SELECT *
            FROM actor;
        """
    },


    {
        "id": "Q1B",
        "group": "projection",
        "title": "Seleccionar todas las columnas sobre tabla grande",
        "objective": "Evaluar el impacto de recuperar todas las columnas.",
        "sql": """
            SELECT *
            FROM actor_big;
        """
    },

    {
        "id": "Q1W",
        "group": "projection",
        "title": "Seleccionar todas las columnas sobre tabla ancha",
        "objective": "Evaluar el impacto de recuperar todas las columnas.",
        "sql": """
            SELECT *
            FROM actor_wide;
        """
    },

    {
        "id": "Q2",
        "group": "projection",
        "title": "Seleccionar columnas necesarias",
        "objective": "Comparar con Q1 utilizando menos columnas.",
        "sql": """
            SELECT first_name, last_name
            FROM actor;
        """
    },

    {
        "id": "Q2B",
        "group": "projection",
        "title": "Seleccionar columnas necesarias sobre tabla grande",
        "objective": "Comparar con Q1 utilizando menos columnas.",
        "sql": """
            SELECT first_name, last_name
            FROM actor_big;
        """
    },

    {
        "id": "Q2W",
        "group": "projection",
        "title": "Seleccionar columnas necesarias sobre tabla ancha",
        "objective": "Comparar con Q1 utilizando menos columnas.",
        "sql": """
            SELECT first_name, last_name
            FROM actor_wide;
        """
    },

    {
        "id": "Q3",
        "group": "filter",
        "title": "Lectura completa de tabla",
        "objective": "Referencia para comparar con un filtro selectivo.",
        "sql": """
            SELECT *
            FROM actor;
        """
    },

    {
        "id": "Q4",
        "group": "filter",
        "title": "Filtro por clave primaria",
        "objective": "Evaluar acceso selectivo.",
        "sql": """
            SELECT *
            FROM actor
            WHERE actor_id = 1;
        """
    },

    {
        "id": "Q5",
        "group": "waste",
        "title": "Filtro poco selectivo",
        "objective": "Analizar trabajo desperdiciado mediante filtrado.",
        "sql": """
            SELECT *
            FROM film
            WHERE length > 180;
        """
    },

    {
        "id": "Q6",
        "group": "waste",
        "title": "Búsqueda por clave primaria",
        "objective": "Comparar con Q5 minimizando filas descartadas.",
        "sql": """
            SELECT *
            FROM film
            WHERE film_id = 1;
        """
    },

    {
        "id": "Q7",
        "group": "join",
        "title": "JOIN film-categoría",
        "objective": "Evaluar coste de JOIN entre tres tablas.",
        "sql": """
            SELECT
                f.title,
                c.name
            FROM film f
            JOIN film_category fc
                ON f.film_id = fc.film_id
            JOIN category c
                ON fc.category_id = c.category_id;
        """
    },

    {
        "id": "Q8",
        "group": "join",
        "title": "JOIN actor-película",
        "objective": "Evaluar un JOIN de mayor complejidad.",
        "sql": """
            SELECT
                a.first_name,
                a.last_name,
                f.title
            FROM actor a
            JOIN film_actor fa
                ON a.actor_id = fa.actor_id
            JOIN film f
                ON fa.film_id = f.film_id;
        """
    },
]


STAR_QUERY = {
    "id": "STAR",
    "group": "didactic",
    "title": "Consulta estrella",
    "objective": (
        "Demostrar trabajo desperdiciado y el valor didáctico "
        "de DuoQuery."
    ),
    "sql": """
        SELECT *
        FROM film
        WHERE title LIKE '%A%';
    """
    }

ALL_QUERIES = BENCHMARK_QUERIES + [STAR_QUERY]


# Indice por id, para resolver las consultas de las parejas didacticas.
QUERIES_POR_ID = {q["id"]: q for q in ALL_QUERIES}


# Parejas del modo guiado de la pestana Comparativa. Reutilizan consultas ya
# validadas del benchmark (no se anade ninguna consulta nueva). Cada pareja lleva
# una explicacion conceptual (el porque invariable); los numeros concretos los
# aporta el veredicto calculado en vivo.
PAREJAS_DIDACTICAS = [
    {
        "concepto": "Proyección · Tabla normal (actor)",
        "a": "Q1",
        "b": "Q2",
        "etiqueta_a": "SELECT *",
        "etiqueta_b": "SELECT first_name, last_name",
        "explicacion": (
            "Ambas consultas leen la tabla completa mediante un Seq Scan y "
            "procesan exactamente el mismo número de páginas de datos. Por eso, el "
            "esfuerzo interno del motor apenas varía al seleccionar menos "
            "columnas.\n\n"
            "La diferencia crítica está en la red: SELECT * aumenta el volumen que "
            "se enviaría al cliente. Como EXPLAIN ANALYZE no mide esa transferencia "
            "por red, los julios del motor parecen similares.\n\n"
            "Lección clave: El coste real de SELECT * no está en la energía de "
            "ejecución, sino en la transferencia de datos que genera."
        ),
    },
    {
        "concepto": "Proyección · Tabla grande (actor_big)",
        "a": "Q1B",
        "b": "Q2B",
        "etiqueta_a": "SELECT *",
        "etiqueta_b": "SELECT first_name, last_name",
        "explicacion": (
            "En un escenario con un volumen elevado de filas, ambas consultas "
            "realizan un Seq Scan completo y procesan las mismas páginas. Por este "
            "motivo, el trabajo interno del motor de datos y su consumo energético "
            "resultan prácticamente idénticos.\n\n"
            "Sin embargo, el volumen de transferencia por red se incrementa "
            "significativamente: SELECT * obliga a enviar todas las columnas por "
            "cada fila recuperada, multiplicando el volumen total transmitido. Como "
            "EXPLAIN ANALYZE no mide esa transferencia por red, los julios no "
            "reflejan esa diferencia.\n\n"
            "Lección clave: En tablas con un gran número de filas, el verdadero "
            "impacto de no seleccionar columnas específicas no está en el "
            "procesamiento interno del motor, sino en el tráfico de red generado."
        ),
    },
    {
        "concepto": "Proyección · Tabla ancha (actor_wide)",
        "a": "Q1W",
        "b": "Q2W",
        "etiqueta_a": "SELECT *",
        "etiqueta_b": "SELECT first_name, last_name",
        "explicacion": (
            "Cuando una tabla contiene columnas de texto o datos de gran tamaño, "
            "la ejecución interna mediante Seq Scan sigue requiriendo un esfuerzo "
            "similar para ambas consultas al recorrer las mismas páginas.\n\n"
            "Sin embargo, el tráfico de red se dispara de manera crítica: SELECT * "
            "obliga a arrastrar el contenido completo de esas columnas pesadas por "
            "cada registro, aunque la aplicación no las necesite. Como EXPLAIN "
            "ANALYZE no mide esa transferencia por red, los julios no reflejan esa "
            "diferencia.\n\n"
            "Lección clave: Cuanto más pesadas son las columnas, más se dispara el "
            "coste de transferencia de SELECT *, aunque el trabajo interno del "
            "motor apenas cambie."
        ),
    },
    {
        "concepto": "Trabajo desperdiciado (Filtro sin índice vs Clave Primaria)",
        "a": "Q5",
        "b": "Q6",
        "etiqueta_a": "WHERE length > 180",
        "etiqueta_b": "WHERE film_id = 1",
        "explicacion": (
            "La consulta con el filtro poco selectivo actúa sobre una columna no "
            "indexada. Para evaluarla, el motor debe recorrer la tabla completa "
            "(Seq Scan) y descartar la gran mayoría de las filas leídas al no "
            "cumplir la condición, lo que genera una sobrecarga ineficiente en el "
            "procesamiento interno del motor.\n\n"
            "En cambio, la consulta por clave primaria accede directamente al "
            "registro buscado mediante el índice (Index Scan), reduciendo al mínimo "
            "el trabajo desperdiciado.\n\n"
            "Lección clave: Leer datos para descartarlos después supone un esfuerzo "
            "ineficiente del motor que impacta directamente en el consumo "
            "energético."
        ),
    },
]
