USE inventario_taller;

-- 1. TABLAS

DROP TABLE IF EXISTS log_movimientos;
DROP TABLE IF EXISTS movimientos;
DROP TABLE IF EXISTS piezas;
DROP TABLE IF EXISTS categorias;
DROP TABLE IF EXISTS tipo;
DROP TABLE IF EXISTS usuarios;

CREATE TABLE usuarios (
    id_usuario  INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(30) NOT NULL UNIQUE,
    contrasena VARCHAR(30) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'Empleado',
    CHECK (rol IN ('Administrador', 'Empleado'))
);

CREATE TABLE categorias (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre_categoria VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE tipo (
    id_tipo INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE piezas (
    id_pieza INT AUTO_INCREMENT PRIMARY KEY,
    nombre_pieza VARCHAR(50) NOT NULL,
    año INT NOT NULL,
    cantidad INT NOT NULL DEFAULT 0,
    descripcion  VARCHAR(100) DEFAULT NULL,
    id_categoria INT NOT NULL,
    id_tipo INT NOT NULL,
    CHECK (cantidad >= 0),
    CHECK (año >= 1900),
    FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (id_tipo) REFERENCES tipo(id_tipo)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE movimientos (
    id_movimiento INT AUTO_INCREMENT PRIMARY KEY,
    id_pieza INT NOT NULL,
    tipo_movimiento VARCHAR(20) NOT NULL,
    cantidad INT NOT NULL,
    fecha DATETIME NOT NULL,
    proveedor VARCHAR(100) DEFAULT NULL,
    FOREIGN KEY (id_pieza) REFERENCES piezas(id_pieza)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE log_movimientos (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    id_pieza INT NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    cantidad INT NOT NULL,
    fecha_log DATETIME NOT NULL,
    descripcion VARCHAR(150)
);


-- 2. DATOS INICIALES

INSERT INTO usuarios (usuario, contrasena, rol) VALUES
('Miguel', 'admin123', 'Administrador'),
('empleado1', '1234', 'Empleado');

INSERT INTO categorias (nombre_categoria) VALUES
('Motor'), ('Monoblocks'), ('Cabezas'), ('Bielas'), ('Pistones'),
('Cigüeñales'), ('Valvulas'), ('Arbol de levas'), ('Bomba de aceite'),
('Bomba de agua'), ('Metales de biela'), ('Metales de centro'),
('Kit de distribucion');

INSERT INTO tipo (nombre_tipo) VALUES
('Carburado'), ('TBI'), ('FI'), ('No aplica');

SELECT * FROM piezas;
INSERT INTO piezas (nombre_pieza, año, cantidad, descripcion, id_categoria, id_tipo) VALUES
('Motor Chevrolet Ecotec 2.4L', 2016, 5,  'Motor 4 cilindros Ecotec Chevrolet', 1, 1),
('Monoblock Ford 302', 2010, 3,  'Monoblock V8 Ford serie 302', 2, 3),
('Cabeza Nissan KA24', 2014, 8,  'Cabeza de 4 cilindros Nissan', 3, 2),
('Biela Honda Civic 1.8L', 2018, 12, 'Biela forjada Honda Civic motor R18', 4, 3),
('Pistón Volkswagen 2.0L', 2015, 4,  'Pistón estándar VW motor 2.0', 5, 1),
('Cigüeñal Toyota 22R', 2012, 2,  'Cigüeñal rectificado Toyota serie 22R', 6, 1),
('Válvula de admisión Mazda', 2017, 20, 'Válvula admisión motor Mazda L3', 7, 3),
('Árbol de levas Dodge 318', 2008, 1,  'Árbol de levas V8 Dodge 318', 8, 1),
('Bomba de aceite GM 2.2L', 2013, 6,  'Bomba de aceite motor GM Ecotec 2.2', 9, 2),
('Bomba de agua Hyundai 2.0', 2019, 7,  'Bomba de agua Hyundai motor G4NA', 10, 3),
('Metales de biela Ford 2.3L', 2016, 15, 'Set metales de biela estándar Ford', 11, 3),
('Metales de centro Chevy 5.7', 2011, 9,  'Set metales de centro Chevrolet 5.7L', 12, 1),
('Kit distribución Kia 1.6L', 2020, 3,  'Kit completo distribución Kia Gamma', 13, 3),
('Pistón Chevrolet 350', 2009, 5,  'Pistón estándar Chevrolet 350 V8', 5, 1),
('Cabeza Ford 5.0L', 2015, 2,  'Cabeza completa Ford Coyote 5.0', 3, 3);

-- 3. FUNCIÓN Y PROCEDIMIENTO

DELIMITER //

-- Función: calcular estado de stock
DROP FUNCTION IF EXISTS fn_estado_stock //
CREATE FUNCTION fn_estado_stock(cantidad INT)
RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN
    DECLARE estado VARCHAR(20);
    IF cantidad <= 5 THEN
        SET estado = 'STOCK BAJO';
    ELSE
        SET estado = 'STOCK NORMAL';
    END IF;
    RETURN estado;
END //

-- Procedimiento: registrar log de movimiento
DROP PROCEDURE IF EXISTS sp_log_movimiento //
CREATE PROCEDURE sp_log_movimiento(
    IN p_id_pieza INT,
    IN p_tipo     VARCHAR(20),
    IN p_cantidad INT
)
BEGIN
    DECLARE desc_log VARCHAR(150);
    SET desc_log = CONCAT('Movimiento de ', p_tipo, ': ', p_cantidad, ' unidades registradas');
    INSERT INTO log_movimientos (id_pieza, tipo, cantidad, descripcion)
    VALUES (p_id_pieza, p_tipo, p_cantidad, desc_log);
END //

DELIMITER ;

-- 4. VISTAS

-- Vista 1: LIKE — búsqueda por nombre de pieza
DROP VIEW IF EXISTS v_busqueda_piezas;
CREATE VIEW v_busqueda_piezas AS
SELECT p.id_pieza, p.nombre_pieza, p.año, p.cantidad,
       c.nombre_categoria, t.nombre_tipo
FROM piezas p
JOIN categorias c ON p.id_categoria = c.id_categoria
JOIN tipo t ON p.id_tipo = t.id_tipo
WHERE p.nombre_pieza LIKE '%Motor%'
   OR p.nombre_pieza LIKE '%Pistón%'
   OR p.nombre_pieza LIKE '%Válvula%';

-- Vista 2: BETWEEN — piezas de años recientes
DROP VIEW IF EXISTS v_piezas_anios_recientes;
CREATE VIEW v_piezas_anios_recientes AS
SELECT p.nombre_pieza, p.año, p.cantidad, c.nombre_categoria
FROM piezas p
JOIN categorias c ON p.id_categoria = c.id_categoria
WHERE p.año BETWEEN 2015 AND 2025;

-- Vista 3: COUNT y SUM — total de piezas por categoría
DROP VIEW IF EXISTS v_total_por_categoria;
CREATE VIEW v_total_por_categoria AS
SELECT c.nombre_categoria,
       COUNT(p.id_pieza) AS total_piezas,
       SUM(p.cantidad)   AS unidades_totales
FROM categorias c
LEFT JOIN piezas p ON c.id_categoria = p.id_categoria
GROUP BY c.nombre_categoria;

-- Vista 4: MAX y MIN — estadísticas de stock por categoría
DROP VIEW IF EXISTS v_estadisticas_stock;
CREATE VIEW v_estadisticas_stock AS
SELECT c.nombre_categoria,
       MAX(p.cantidad) AS stock_maximo,
       MIN(p.cantidad) AS stock_minimo
FROM piezas p
JOIN categorias c ON p.id_categoria = c.id_categoria
GROUP BY c.nombre_categoria;

-- Vista 5: inventario completo con estado (3 tablas + función)
DROP VIEW IF EXISTS v_inventario_completo;
CREATE VIEW v_inventario_completo AS
SELECT p.id_pieza, p.nombre_pieza, p.año, p.cantidad,
       p.descripcion, c.nombre_categoria, t.nombre_tipo,
       fn_estado_stock(p.cantidad) AS estado_stock
FROM piezas p
JOIN categorias c ON p.id_categoria = c.id_categoria
JOIN tipo t ON p.id_tipo = t.id_tipo;

-- 5. USUARIO SPIDER

CREATE USER 'Spider'@'%' IDENTIFIED BY 'anonimo';
GRANT INSERT, DELETE ON inventario_taller.* TO 'Spider'@'%';
FLUSH PRIVILEGES;

SELECT * FROM inventario_taller.v_inventario_completo;
