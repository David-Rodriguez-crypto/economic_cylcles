import requests
import mysql.connector


# ==========================================
# CONFIGURACIÓN
# ==========================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "D6763610",
    "database": "economic_cycles",
    "port": 3306
}

INDICATOR = "NY.GDP.MKTP.KD"

START_YEAR = 2000


COUNTRIES = {
    "COL": "Colombia",
    "ARG": "Argentina",
    "BOL": "Bolivia",
    "BRA": "Brasil",
    "CHL": "Chile",
    "ECU": "Ecuador",
    "MEX": "México",
    "PRY": "Paraguay",
    "PER": "Perú",
    "URY": "Uruguay",
    "USA": "Estados Unidos"
}


# ==========================================
# CONEXIÓN MYSQL
# ==========================================

def get_connection():

    return mysql.connector.connect(**DB_CONFIG)


# ==========================================
# OBTENER DATOS DEL BANCO MUNDIAL
# ==========================================

def get_world_bank_data(country_code):

    url = (
        f"https://api.worldbank.org/v2/country/"
        f"{country_code}/indicator/{INDICATOR}"
        f"?format=json&per_page=100"
    )

    response = requests.get(url, timeout=30)

    response.raise_for_status()

    data = response.json()

    if len(data) < 2 or data[1] is None:
        return []

    results = []

    for row in data[1]:

        if row["value"] is None:
            continue

        year = int(row["date"])

        if year < START_YEAR:
            continue

        value = float(row["value"])

        results.append({
            "year": year,
            "value": value
        })

    results.sort(key=lambda x: x["year"])

    return results


# ==========================================
# OBTENER / CREAR PAÍS
# ==========================================

def get_or_create_country(cursor, code, name):

    cursor.execute(
        """
        SELECT id
        FROM countries
        WHERE code = %s
        """,
        (code,)
    )

    result = cursor.fetchone()

    if result:

        return result[0]

    cursor.execute(
        """
        INSERT INTO countries (name, code)
        VALUES (%s, %s)
        """,
        (name, code)
    )

    return cursor.lastrowid


# ==========================================
# INSERTAR DATOS DEL PIB
# ==========================================

def insert_gdp_data(cursor, country_id, data):

    inserted = 0
    skipped = 0

    for row in data:

        cursor.execute(
            """
            SELECT id
            FROM gdp_data
            WHERE country_id = %s
              AND year = %s
            """,
            (
                country_id,
                row["year"]
            )
        )

        exists = cursor.fetchone()

        if exists:

            skipped += 1

            continue

        cursor.execute(
            """
            INSERT INTO gdp_data
                (country_id, year, value)
            VALUES
                (%s, %s, %s)
            """,
            (
                country_id,
                row["year"],
                row["value"]
            )
        )

        inserted += 1

    return inserted, skipped


# ==========================================
# PROCESO PRINCIPAL
# ==========================================

def main():

    print("=" * 50)
    print("IMPORTADOR DE PIB - BANCO MUNDIAL")
    print("=" * 50)

    connection = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        print("\nConexión a MySQL exitosa.\n")

        for code, name in COUNTRIES.items():

            print(f"Procesando {name} ({code})...")

            try:

                data = get_world_bank_data(code)

                if not data:

                    print("  No se encontraron datos.\n")

                    continue

                country_id = get_or_create_country(
                    cursor,
                    code,
                    name
                )

                inserted, skipped = insert_gdp_data(
                    cursor,
                    country_id,
                    data
                )

                connection.commit()

                print(
                    f"  Datos encontrados: {len(data)}"
                )

                print(
                    f"  Insertados: {inserted}"
                )

                print(
                    f"  Ya existentes: {skipped}"
                )

                print(
                    f"  Último año disponible: "
                    f"{data[-1]['year']}"
                )

                print()

            except Exception as e:

                connection.rollback()

                print(
                    f"  ERROR con {name}: {e}\n"
                )

        cursor.close()

        print("=" * 50)
        print("IMPORTACIÓN FINALIZADA")
        print("=" * 50)

    except Exception as e:

        print("\nERROR GENERAL:")
        print(e)

    finally:

        if connection and connection.is_connected():

            connection.close()

            print("\nConexión cerrada.")


# ==========================================
# EJECUTAR
# ==========================================

if __name__ == "__main__":
    main()