-- Seleccionar la base de datos especificada en el docker-compose
USE clients_db;

-- 1. Crear tabla padre (clientes)
CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    telefono VARCHAR(50),
    dni VARCHAR(20) NOT NULL,
    fecha_registro DATETIME NOT NULL,
    activo TINYINT(1) DEFAULT 1
);

-- 2. Crear tabla hija (direcciones)
CREATE TABLE IF NOT EXISTS direcciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    calle VARCHAR(255) NOT NULL,
    distrito VARCHAR(100),
    ciudad VARCHAR(100),
    codigo_postal VARCHAR(20),
    referencia TEXT,
    tipo VARCHAR(50),
    es_principal TINYINT(1) DEFAULT 1,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
);
