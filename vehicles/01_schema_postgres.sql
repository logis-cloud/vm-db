-- PostgreSQL se conecta automáticamente a db_inventario según el docker-compose

CREATE SEQUENCE IF NOT EXISTS vehiculos_id_vehiculo_seq
    START WITH 1
    INCREMENT BY 50;   -- debe coincidir con allocationSize=50 de @SequenceGenerator

CREATE TABLE IF NOT EXISTS vehiculos (
    id_vehiculo BIGINT PRIMARY KEY DEFAULT nextval('vehiculos_id_vehiculo_seq'),
    marca VARCHAR(50),
    modelo VARCHAR(50),
    placa VARCHAR(10) UNIQUE NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    anio_fabricacion INT,
    capacidad_kg NUMERIC(10, 2) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER SEQUENCE vehiculos_id_vehiculo_seq OWNED BY vehiculos.id_vehiculo;

CREATE SEQUENCE IF NOT EXISTS conductores_id_conductor_seq
    START WITH 1
    INCREMENT BY 50;   -- debe coincidir con allocationSize=50 de @SequenceGenerator

CREATE TABLE IF NOT EXISTS conductores (
    id_conductor BIGINT PRIMARY KEY DEFAULT nextval('conductores_id_conductor_seq'),
    nombre VARCHAR(80) NOT NULL,
    apellido VARCHAR(80) NOT NULL,
    dni VARCHAR(15) UNIQUE NOT NULL,
    nro_licencia VARCHAR(20) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    turno VARCHAR(10) NOT NULL,
    fecha_contratacion DATE,
    activo BOOLEAN DEFAULT TRUE,
    id_vehiculo BIGINT NULL,
    CONSTRAINT fk_vehiculo FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo) ON DELETE SET NULL
);

ALTER SEQUENCE conductores_id_conductor_seq OWNED BY conductores.id_conductor;
