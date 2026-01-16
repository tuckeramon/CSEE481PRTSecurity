CREATE DATABASE `prtdb`/*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
 
USE prtdb;

CREATE TABLE `prtcarts` (
  `barcode` char(4) NOT NULL,
  `destination` tinyint unsigned NOT NULL,
  PRIMARY KEY (`barcode`),
  UNIQUE KEY `barcode_UNIQUE` (`barcode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `prtsorterreport` (
  `idPRTSorterReport` int unsigned NOT NULL AUTO_INCREMENT,
  `sorterID` tinyint unsigned NOT NULL,
  `barcode` char(4) DEFAULT NULL,
  `active` tinyint unsigned NOT NULL,
  `lost` tinyint unsigned NOT NULL,
  `good` tinyint unsigned NOT NULL,
  `diverted` tinyint unsigned NOT NULL,
  `time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idPRTSorterReport`),
  KEY `prtCartBarcodeID_idx` (`barcode`),
  CONSTRAINT `prtCartBarcodeID` FOREIGN KEY (`barcode`) REFERENCES `prtcarts` (`barcode`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `prtsorterrequest` (
  `idPRTSorterRequest` int unsigned NOT NULL AUTO_INCREMENT,
  `sorterID` tinyint unsigned NOT NULL,
  `transactionID` tinyint unsigned NOT NULL,
  `barcode` char(4) NOT NULL,
  `time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idPRTSorterRequest`),
  UNIQUE KEY `idPRTSorterRequest_UNIQUE` (`idPRTSorterRequest`),
  KEY `prtCartBarcodeID_idx` (`barcode`),
  CONSTRAINT `prtCartBarcodeID_sr` FOREIGN KEY (`barcode`) REFERENCES `prtcarts` (`barcode`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `prtsorterresponse` (
  `idPRTSorterResponse` int unsigned NOT NULL AUTO_INCREMENT,
  `sorterID` tinyint unsigned NOT NULL,
  `barcode` char(4) NOT NULL,
  `transactionID` tinyint unsigned NOT NULL,
  `destination` tinyint unsigned NOT NULL,
  `time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idPRTSorterResponse`),
  UNIQUE KEY `idPRTSorterResponse_UNIQUE` (`idPRTSorterResponse`),
  KEY `prtCartBarcodeID_idx` (`barcode`),
  CONSTRAINT `prtCartBarcodeID_sres` FOREIGN KEY (`barcode`) REFERENCES `prtcarts` (`barcode`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `prtremovecart` (
 `barcode` char(4) NOT NULL,
 `area` tinyint unsigned NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


SELECT * FROM PRTCARTS;
SELECT * FROM PRTSORTERREPORT;
SELECT * FROM PRTSORTERREQUEST;
SELECT * FROM PRTSORTERRESPONSE;
SELECT * FROM PRTREMOVECART;