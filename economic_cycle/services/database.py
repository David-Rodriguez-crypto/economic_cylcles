
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():

    config = {
        "host": os.environ.get("TIDB_HOST"),
        "user": os.environ.get("TIDB_USER"),
        "password": os.environ.get("TIDB_PASSWORD"),
        "database": os.environ.get("TIDB_DATABASE", "economic_cycles"),
        "port": int(os.environ.get("TIDB_PORT", "4000")),
        "connection_timeout": 20
    }

    ca_path = os.environ.get("TIDB_SSL_CA")

    if ca_path:
        config["ssl_ca"] = ca_path
        config["ssl_verify_cert"] = True
        config["ssl_verify_identity"] = True

    return mysql.connector.connect(**config)


def get_countries():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, name, code
            FROM countries
            ORDER BY name
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def create_country(name, code):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO countries (name, code)
            VALUES (%s, %s)
        """, (name, code))

        connection.commit()
        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def save_gdp(country_id, year, value):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO gdp_data (country_id, year, value)
            VALUES (%s, %s, %s)
        """, (country_id, year, value))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_gdp_by_country(country_id):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT year, value
            FROM gdp_data
            WHERE country_id = %s
            ORDER BY year
        """, (country_id,))

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def save_gdp_bulk(country_id, records):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.executemany("""
            INSERT INTO gdp_data (country_id, year, value)
            VALUES (%s, %s, %s)
        """, [
            (country_id, year, value)
            for year, value in records
        ])

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_or_create_country(name, code):

    name = name.strip()
    code = code.strip().upper()

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, name, code
            FROM countries
            WHERE code = %s
        """, (code,))

        country = cursor.fetchone()

        if country:
            if country["name"].strip().casefold() != name.casefold():
                raise ValueError(
                    f"El código {code} ya pertenece a "
                    f"{country['name']}. Comprueba el nombre y el código."
                )

            return country["id"]

        cursor.execute("""
            INSERT INTO countries (name, code)
            VALUES (%s, %s)
        """, (name, code))

        connection.commit()
        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()
