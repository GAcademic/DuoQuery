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
