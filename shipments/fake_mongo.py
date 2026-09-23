import os
import random
from datetime import datetime, timedelta

import pymongo
import pymysql
import psycopg2
from faker import Faker

fake = Faker("es_ES")

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://root:root123@localhost:27017/shipments_db?authSource=admin",
)

MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "root123"),
    "database": os.environ.get("MYSQL_DB", "clients_db"),
}

PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", "5432")),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD", "postgres123"),
    "dbname": os.environ.get("PG_DB", "vehicles_db"),
}

TOTAL_ENVIOS = 20000
BATCH_SIZE = 1000

ESTADOS_ENVIO = ["CREADO", "EN_TRANSITO", "ENTREGADO", "CANCELADO"]


def obtener_clientes_con_direccion():
    print("1/3. Consultando clientes activos y sus direcciones desde MySQL...")

    conn = pymysql.connect(**MYSQL_CONFIG)

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    c.id AS cliente_id,
                    d.calle,
                    d.distrito,
                    d.ciudad,
                    d.codigo_postal AS codigo_postal,
                    d.referencia
                FROM clientes c
                INNER JOIN direcciones d
                    ON c.id = d.cliente_id
                WHERE c.activo = 1
                """
            )
            clientes = cursor.fetchall()
    finally:
        conn.close()

    if not clientes:
        raise RuntimeError(
            "No se encontraron clientes activos con dirección en MySQL."
        )

    print(f"  -> {len(clientes)} registros de direcciones disponibles.")
    return clientes


def obtener_vehiculos_conductores():
    print(
        "2/3. Consultando vehículos disponibles y conductores activos "
        "desde PostgreSQL..."
    )

    conn = psycopg2.connect(**PG_CONFIG)

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    v.id_vehiculo AS id_vehiculo,
                    v.placa,
                    v.tipo,
                    v.marca,
                    v.modelo,
                    c.id_conductor AS id_conductor,
                    c.nombre,
                    c.apellido,
                    c.dni,
                    c.turno
                FROM vehiculos v
                INNER JOIN conductores c
                    ON v.id_vehiculo = c.id_vehiculo
                WHERE v.estado = 'DISPONIBLE'
                  AND c.activo = TRUE
                """
            )

            vehiculos = [
                {
                    "id_vehiculo": row[0],
                    "placa": row[1],
                    "tipo": row[2],
                    "marca": row[3],
                    "modelo": row[4],
                    "id_conductor": row[5],
                    "nombre": row[6],
                    "apellido": row[7],
                    "dni": row[8],
                    "turno": row[9],
                }
                for row in cursor.fetchall()
            ]
    finally:
        conn.close()

    if not vehiculos:
        raise RuntimeError(
            "No se encontraron vehículos DISPONIBLES con conductores activos "
            "en PostgreSQL."
        )

    print(f"  -> {len(vehiculos)} combinaciones vehículo + conductor disponibles.")
    return vehiculos


def generar_item():
    return {
        "sku": f"SKU-{random.randint(1, 999):03d}",
        "descripcion": fake.catch_phrase(),
        "cantidad": random.randint(1, 4),
        "pesoKg": round(random.uniform(0.5, 12.0), 1),
    }


def generar_envio(cliente, vehiculo):
    fecha_creacion = fake.date_time_between(
        start_date="-1y",
        end_date="now",
    )

    return {
        "codigoSeguimiento": (
            f"LOG-{fake.unique.bothify(text='????????').upper()}"
        ),
        "clienteId": cliente["cliente_id"],
        "pedidoId": f"PED-{random.randint(1000, 9999)}",
        "estado": random.choice(ESTADOS_ENVIO),
        "direccionEntrega": {
            "calle": cliente["calle"],
            "distrito": cliente["distrito"],
            "ciudad": cliente["ciudad"] or "Lima",
            "codigoPostal": cliente["codigo_postal"] or "15036",
            "referencia": cliente["referencia"] or "Sin referencia",
        },
        "items": [generar_item()],
        "vehiculoAsignado": {
            "idVehiculo": vehiculo["id_vehiculo"],
            "placa": vehiculo["placa"],
            "tipo": vehiculo["tipo"],
            "marca": vehiculo["marca"],
            "modelo": vehiculo["modelo"],
        },
        "conductorAsignado": {
            "idConductor": vehiculo["id_conductor"],
            "nombre": vehiculo["nombre"],
            "apellido": vehiculo["apellido"],
            "dni": vehiculo["dni"],
            "turno": vehiculo["turno"],
        },
        "fechaCreacion": fecha_creacion,
        "fechaActualizacion": datetime.now(),
    }


def poblar_mongodb(clientes, vehiculos):
    print(f"3/3. Generando {TOTAL_ENVIOS} envíos en MongoDB...")

    mongo_client = pymongo.MongoClient(MONGO_URI)
    db = mongo_client["shipments_db"]
    collection = db["envios"]

    try:
        # El seed de envíos es reproducible: al volver a ejecutarlo se
        # reemplaza la data fake anterior en lugar de duplicarla.
        eliminados = collection.delete_many({}).deleted_count
        if eliminados:
            print(f"  -> Se eliminaron {eliminados} envíos anteriores.")

        collection.create_index("codigoSeguimiento", unique=True)
        collection.create_index("clienteId")
        collection.create_index("estado")

        for inicio in range(0, TOTAL_ENVIOS, BATCH_SIZE):
            cantidad = min(BATCH_SIZE, TOTAL_ENVIOS - inicio)

            batch = [
                generar_envio(
                    random.choice(clientes),
                    random.choice(vehiculos),
                )
                for _ in range(cantidad)
            ]

            collection.insert_many(batch, ordered=False)

            print(
                f"  -> {inicio + cantidad} / {TOTAL_ENVIOS} "
                "envíos insertados..."
            )
    finally:
        mongo_client.close()


def main():
    print("=== Iniciando data fake para MongoDB / envíos ===")

    clientes = obtener_clientes_con_direccion()
    vehiculos = obtener_vehiculos_conductores()
    poblar_mongodb(clientes, vehiculos)

    print("¡Poblamiento de envíos finalizado con éxito!")


if __name__ == "__main__":
    main()
