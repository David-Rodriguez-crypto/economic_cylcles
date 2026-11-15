
import os
import mysql.connector
from dotenv import load_dotenv
import tempfile

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

    ca_value = (
        os.environ.get("TIDB_SSL_CA_CONTENT")
        or os.environ.get("TIDB_SSL_CA")
    )
    if ca_value:
        if os.path.isfile(ca_value):
            ca_path = ca_value
        else:
            ca_path = os.path.join(
                tempfile.gettempdir(),
                "tidb-ca.pem"
            )

            with open(ca_path, "w", encoding="utf-8") as cert_file:
                cert_file.write(ca_value.strip() + "\n")

        config["ssl_ca"] = ca_path
        config["ssl_verify_cert"] = True
        config["ssl_verify_identity"] = True
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
        # Reservar un identificador nuevo
        cursor.execute("""
            UPDATE id_sequences
            SET next_id = next_id + 1
            WHERE name = 'gdp_data'
        """)

        cursor.execute("""
            SELECT next_id
            FROM id_sequences
            WHERE name = 'gdp_data'
        """)

        new_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO gdp_data (id, country_id, year, value)
            VALUES (%s, %s, %s, %s)
        """, (new_id, country_id, year, value))

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

    records = list(records)

    if not records:
        return

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Reservar todos los identificadores necesarios
        cursor.execute("""
            UPDATE id_sequences
            SET next_id = next_id + %s
            WHERE name = 'gdp_data'
        """, (len(records),))

        cursor.execute("""
            SELECT next_id
            FROM id_sequences
            WHERE name = 'gdp_data'
        """)

        last_id = cursor.fetchone()[0]
        first_id = last_id - len(records) + 1

        data = [
            (first_id + i, country_id, year, value)
            for i, (year, value) in enumerate(records)
        ]

        cursor.executemany("""
            INSERT INTO gdp_data (id, country_id, year, value)
            VALUES (%s, %s, %s, %s)
        """, data)

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
