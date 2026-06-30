-- MySQL dump 10.13  Distrib 8.4.9, for Linux (x86_64)
--
-- Host: localhost    Database: huerto_iot
-- ------------------------------------------------------
-- Server version	8.4.9

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `huerto_iot`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `huerto_iot` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `huerto_iot`;

--
-- Table structure for table `alertas`
--

DROP TABLE IF EXISTS `alertas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alertas` (
  `uuid_alerta` char(36) NOT NULL DEFAULT (uuid()),
  `uuid_cultivo` char(36) NOT NULL,
  `tipo_alerta` varchar(50) NOT NULL,
  `mensaje` text NOT NULL,
  `leida` tinyint(1) NOT NULL DEFAULT '0',
  `agua` tinyint(1) NOT NULL DEFAULT '0',
  `momento_alerta` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`uuid_alerta`),
  KEY `alertas_cultivo_fk` (`uuid_cultivo`),
  CONSTRAINT `alertas_cultivo_fk` FOREIGN KEY (`uuid_cultivo`) REFERENCES `cultivo` (`uuid_cultivo`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alertas`
--

LOCK TABLES `alertas` WRITE;
/*!40000 ALTER TABLE `alertas` DISABLE KEYS */;
/*!40000 ALTER TABLE `alertas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `conf_umbrales`
--

DROP TABLE IF EXISTS `conf_umbrales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `conf_umbrales` (
  `uuid_conf` char(36) NOT NULL DEFAULT (uuid()),
  `uuid_cultivo` char(36) NOT NULL,
  `tipo_sensor` varchar(50) NOT NULL,
  `min_valor` float NOT NULL,
  `max_valor` float NOT NULL,
  PRIMARY KEY (`uuid_conf`),
  UNIQUE KEY `conf_umbrales_uuid_cultivo_tipo_sensor_unique` (`uuid_cultivo`,`tipo_sensor`),
  CONSTRAINT `conf_umbrales_cultivo_fk` FOREIGN KEY (`uuid_cultivo`) REFERENCES `cultivo` (`uuid_cultivo`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `conf_umbrales_valores_check` CHECK ((`min_valor` <= `max_valor`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `conf_umbrales`
--

LOCK TABLES `conf_umbrales` WRITE;
/*!40000 ALTER TABLE `conf_umbrales` DISABLE KEYS */;
/*!40000 ALTER TABLE `conf_umbrales` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cultivo`
--

DROP TABLE IF EXISTS `cultivo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cultivo` (
  `uuid_cultivo` char(36) NOT NULL DEFAULT (uuid()),
  `user_uuid` char(36) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `secreto_cifrado` varchar(255) NOT NULL,
  `estado_del_cultivo` enum('activo','inactivo') DEFAULT 'activo',
  `fecha_creacion` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `api_key_hash` varchar(64) NOT NULL,
  PRIMARY KEY (`uuid_cultivo`),
  UNIQUE KEY `cultivo_api_key_hash_unique` (`api_key_hash`),
  KEY `cultivo_usuario_fk` (`user_uuid`),
  CONSTRAINT `cultivo_usuario_fk` FOREIGN KEY (`user_uuid`) REFERENCES `usuario` (`user_uuid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cultivo`
--

LOCK TABLES `cultivo` WRITE;
/*!40000 ALTER TABLE `cultivo` DISABLE KEYS */;
/*!40000 ALTER TABLE `cultivo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `logs_riego`
--

DROP TABLE IF EXISTS `logs_riego`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `logs_riego` (
  `uuid_comando` char(36) NOT NULL DEFAULT (uuid()),
  `uuid_cultivo` char(36) NOT NULL,
  `origen` varchar(50) NOT NULL,
  `accion` varchar(100) NOT NULL,
  `momento` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`uuid_comando`),
  KEY `logs_riego_cultivo_fk` (`uuid_cultivo`),
  CONSTRAINT `logs_riego_cultivo_fk` FOREIGN KEY (`uuid_cultivo`) REFERENCES `cultivo` (`uuid_cultivo`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `logs_riego`
--

LOCK TABLES `logs_riego` WRITE;
/*!40000 ALTER TABLE `logs_riego` DISABLE KEYS */;
/*!40000 ALTER TABLE `logs_riego` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `user_uuid` char(36) NOT NULL DEFAULT (uuid()),
  `email` varchar(100) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `fecha_registro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_uuid`),
  UNIQUE KEY `usuario_email_unique` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario`
--

LOCK TABLES `usuario` WRITE;
/*!40000 ALTER TABLE `usuario` DISABLE KEYS */;
INSERT INTO `usuario` VALUES ('afde07ac-6332-11f1-aa13-f6e74fb046f3','1@2','Prueba','scrypt:32768:8:1$VPfsAbbMMR2VAZQ5$f2d9b520320c012177e8e9e809c12ff5008fad780bbacbdfac3447d6a89d2adedb36cadc3bb530c8f585cf786b21cbcf228889e325ceef1e5b7dd1f9e4fbe178','2026-06-08 12:07:57');
/*!40000 ALTER TABLE `usuario` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-08 12:08:12
