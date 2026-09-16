import os
import random

import psycopg2
from psycopg2.extras import execute_values
from faker import Faker

fake = Faker('es_ES')

# Config por variables de entorno, con los mismos nombres y defaults que usa
# el resto del proyecto (.env.example del microservicio). Evita el típico
# error de que el seed puebla una base distinta a la que usa el API.
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres123'),
    'dbname': os.environ.get('DB_NAME', 'vehicles_db'),
}

TOTAL_VEHICULOS = 20000
BATCH_SIZE = 1000

MARCAS = ['Toyota', 'Hyundai', 'Volvo', 'Scania', 'Mercedes-Benz', 'Isuzu', 'Nissan']
TIPOS = ['MOTO', 'FURGONETA', 'CAMION']
ESTADOS = ['DISPONIBLE', 'EN_RUTA', 'MANTENIMIENTO', 'INACTIVO']
TURNOS = ['MANANA', 'TARDE', 'NOCHE']

SQL_VEHICULOS = """
    INSERT INTO vehiculos (marca, modelo, placa, tipo, anio_fabricacion, capacidad_kg, estado)
    VALUES %s
    RETURNING id_vehiculo;
"""

SQL_CONDUCTORES = """
    INSERT INTO conductores
        (id_vehiculo, nombre, apellido, dni, nro_licencia, telefono, turno, fecha_contratacion, activo)
    VALUES %s;
"""


def telefono_valido():
    """fake.phone_number() a veces excede VARCHAR(20) (extensiones, etc.);
    lo truncamos para no tumbar el batch entero."""
    return fake.phone_number()[:20]


def generar_vehiculo(idx):
    return (
        random.choice(MARCAS),
        fake.word().capitalize(),
        f"V{idx + 1:06d}",
        random.choice(TIPOS),
        random.randint(2015, 2024),
        round(random.uniform(1500.0, 15000.0), 2),
        random.choice(ESTADOS),
    )


def generar_conductor(id_vehiculo):
    return (
        id_vehiculo,
        fake.first_name(),
        fake.last_name(),
        fake.unique.numerify('########'),
        fake.unique.bothify(text='Q-########'),
        telefono_valido(),
        random.choice(TURNOS),
        fake.date_between(start_date='-5y', end_date='today'),
        True,
    )


def reset_tablas(cursor):
    print("Vaciando vehiculos y conductores (TRUNCATE ... RESTART IDENTITY)...")
    cursor.execute("TRUNCATE TABLE conductores, vehiculos RESTART IDENTITY CASCADE;")


def poblar_vehiculos(cursor):
    vehiculo_ids = []
    print(f"Cargando {TOTAL_VEHICULOS} vehículos...")
    for i in range(0, TOTAL_VEHICULOS, BATCH_SIZE):
        batch = [generar_vehiculo(idx) for idx in range(i, i + BATCH_SIZE)]
        ids_batch = execute_values(cursor, SQL_VEHICULOS, batch, fetch=True)
        vehiculo_ids.extend(row[0] for row in ids_batch)
        print(f"  -> {len(vehiculo_ids)} vehículos insertados...")
    return vehiculo_ids


def poblar_conductores(cursor, vehiculo_ids):
    print("Cargando conductores...")
    batch = []
    total = 0
    for v_id in vehiculo_ids:
        num_conductores = random.choices([1, 2], weights=[0.85, 0.15])[0]
        for _ in range(num_conductores):
            batch.append(generar_conductor(v_id))
            if len(batch) >= BATCH_SIZE:
                execute_values(cursor, SQL_CONDUCTORES, batch)
                total += len(batch)
                print(f"  -> {total} conductores insertados...")
                batch = []
    if batch:
        execute_values(cursor, SQL_CONDUCTORES, batch)
        total += len(batch)
        print(f"  -> {total} conductores insertados...")


def populate_postgres(reset: bool = True):
    print("Conectando a PostgreSQL...")
    print(f"  host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['dbname']}")
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            if reset:
                reset_tablas(cursor)
            vehiculo_ids = poblar_vehiculos(cursor)
            conn.commit()

            poblar_conductores(cursor, vehiculo_ids)
            conn.commit()
        print("¡Poblamiento finalizado con éxito en PostgreSQL!")
    except Exception:
        conn.rollback()
        print("Ocurrió un error, se hizo rollback de la transacción en curso.")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    populate_postgres()
