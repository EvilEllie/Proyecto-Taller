-- MySQL dump 10.10
--
-- Host: localhost    Database: inventario_taller
-- ------------------------------------------------------
-- Server version	5.1.65-community

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `categorias`
--

DROP TABLE IF EXISTS `categorias`;
CREATE TABLE `categorias` (
  `id_categoria` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_categoria` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `categorias`
--


/*!40000 ALTER TABLE `categorias` DISABLE KEYS */;
LOCK TABLES `categorias` WRITE;
INSERT INTO `categorias` VALUES (1,'Motor'),(2,'Monoblocks'),(3,'Cabezas'),(4,'Bielas'),(5,'Pistones'),(6,'Cigüeñales'),(7,'Valvulas'),(8,'Arbol de levas'),(9,'Bomba de aceite'),(10,'Bomba de agua'),(11,'Metales de biela'),(12,'Metales de centro'),(13,'Kit de distribucion');
UNLOCK TABLES;
/*!40000 ALTER TABLE `categorias` ENABLE KEYS */;

--
-- Table structure for table `movimientos`
--

DROP TABLE IF EXISTS `movimientos`;
CREATE TABLE `movimientos` (
  `id_movimiento` int(11) NOT NULL AUTO_INCREMENT,
  `id_pieza` int(11) DEFAULT NULL,
  `tipo_movimiento` varchar(20) DEFAULT NULL,
  `cantidad` int(11) DEFAULT NULL,
  `fecha` datetime DEFAULT NULL,
  PRIMARY KEY (`id_movimiento`),
  KEY `id_pieza` (`id_pieza`),
  CONSTRAINT `movimientos_ibfk_1` FOREIGN KEY (`id_pieza`) REFERENCES `piezas` (`id_pieza`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `movimientos`
--


/*!40000 ALTER TABLE `movimientos` DISABLE KEYS */;
LOCK TABLES `movimientos` WRITE;
INSERT INTO `movimientos` VALUES (4,3,'SALIDA',2,'2026-02-21 22:14:25'),(5,3,'ENTRADA',5,'2026-02-21 22:15:02'),(6,3,'SALIDA',2,'2026-02-21 23:03:22');
UNLOCK TABLES;
/*!40000 ALTER TABLE `movimientos` ENABLE KEYS */;

/*!50003 SET @OLD_SQL_MODE=@@SQL_MODE*/;
DELIMITER ;;
/*!50003 SET SESSION SQL_MODE="STRICT_TRANS_TABLES,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION" */;;
/*!50003 CREATE */ /*!50017 DEFINER=`root`@`localhost` */ /*!50003 TRIGGER `actualizar_stock` AFTER INSERT ON `movimientos` FOR EACH ROW BEGIN
  IF NEW.tipo_movimiento = 'ENTRADA' THEN
    UPDATE piezas
    SET cantidad = cantidad + NEW.cantidad
    WHERE id_pieza = NEW.id_pieza;
  END IF;

  IF NEW.tipo_movimiento = 'SALIDA' THEN
    UPDATE piezas
    SET cantidad = cantidad - NEW.cantidad
    WHERE id_pieza = NEW.id_pieza;
  END IF;
END */;;

DELIMITER ;
/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE */;

--
-- Table structure for table `piezas`
--

DROP TABLE IF EXISTS `piezas`;
CREATE TABLE `piezas` (
  `id_pieza` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_pieza` varchar(50) DEFAULT NULL,
  `año` int(11) DEFAULT NULL,
  `cantidad` int(11) DEFAULT NULL,
  `descripcion` varchar(100) DEFAULT NULL,
  `id_categoria` int(11) DEFAULT NULL,
  `id_tipo` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_pieza`),
  KEY `id_categoria` (`id_categoria`),
  KEY `id_tipo` (`id_tipo`),
  CONSTRAINT `piezas_ibfk_1` FOREIGN KEY (`id_categoria`) REFERENCES `categorias` (`id_categoria`),
  CONSTRAINT `piezas_ibfk_2` FOREIGN KEY (`id_tipo`) REFERENCES `tipo` (`id_tipo`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `piezas`
--


/*!40000 ALTER TABLE `piezas` DISABLE KEYS */;
LOCK TABLES `piezas` WRITE;
INSERT INTO `piezas` VALUES (3,'Motor Chevrolet Ecotec 2.4L',2016,3,'Motor 4 cilindros Ecotec Chevrolet',1,1);
UNLOCK TABLES;
/*!40000 ALTER TABLE `piezas` ENABLE KEYS */;

--
-- Table structure for table `tipo`
--

DROP TABLE IF EXISTS `tipo`;
CREATE TABLE `tipo` (
  `id_tipo` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_tipo` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_tipo`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `tipo`
--


/*!40000 ALTER TABLE `tipo` DISABLE KEYS */;
LOCK TABLES `tipo` WRITE;
INSERT INTO `tipo` VALUES (1,'Carburado'),(2,'Carburado'),(3,'TBI'),(4,'FI');
UNLOCK TABLES;
/*!40000 ALTER TABLE `tipo` ENABLE KEYS */;

--
-- Table structure for table `tipo_pieza`
--

DROP TABLE IF EXISTS `tipo_pieza`;
CREATE TABLE `tipo_pieza` (
  `id_tipo` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_tipo` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_tipo`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `tipo_pieza`
--


/*!40000 ALTER TABLE `tipo_pieza` DISABLE KEYS */;
LOCK TABLES `tipo_pieza` WRITE;
UNLOCK TABLES;
/*!40000 ALTER TABLE `tipo_pieza` ENABLE KEYS */;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE `usuarios` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `usuario` varchar(30) DEFAULT NULL,
  `contrasena` varchar(30) DEFAULT NULL,
  `rol` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `usuarios`
--


/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
LOCK TABLES `usuarios` WRITE;
INSERT INTO `usuarios` VALUES (1,'Miguel','admin123','Administrador'),(2,'empleado1','1234','Empleado');
UNLOCK TABLES;
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

