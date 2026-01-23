/*
 * SQL Setup Script - Creates NEW Database (prt_unified)
 *
 * This creates a completely NEW database that won't affect:
 *   - prtdb (old backend database)
 *   - prt_system (old frontend database)
 *   - Any other existing databases
 *
 * Database name: prt_unified
 *
 * Run with: mysql -u root -p < setup_new_database.sql
 *
 * IMPORTANT: After running this, update main.py config to use 'prt_unified':
 *   config = {
 *       'host': 'localhost',
 *       'user': 'root',
 *       'password': 'root',
 *       'database': 'prt_unified'  <-- Change this
 *   }
 */

-- ============================================================================
-- CREATE NEW DATABASE: prt_unified
-- ============================================================================

CREATE DATABASE prt_unified;
USE prt_unified;

SELECT '=== Created new database: prt_unified ===' AS status;

-- ============================================================================
-- FRONTEND TABLES
-- ============================================================================

-- Users table for authentication
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cart activity logs (auto-populated by backend via PRTDB.log_to_cart_logs())
CREATE TABLE cart_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cart_id INT NOT NULL,
    position VARCHAR(50) NOT NULL,
    event VARCHAR(100) NOT NULL,
    action_type VARCHAR(50) DEFAULT NULL,
    time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cart_id (cart_id),
    INDEX idx_time_stamp (time_stamp)
);

-- ============================================================================
-- BACKEND TABLES (PLC Communication)
-- ============================================================================

-- Sorter requests from PLC
CREATE TABLE PRTSorterRequest (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sorterID INT NOT NULL,
    transactionID INT NOT NULL,
    barcode VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sorter responses to PLC
CREATE TABLE PRTSorterResponse (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sorterID INT NOT NULL,
    barcode VARCHAR(10) NOT NULL,
    transactionID INT NOT NULL,
    destination INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sorter status reports
CREATE TABLE PRTSorterReport (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sorterID INT NOT NULL,
    barcode VARCHAR(10) NOT NULL,
    active TINYINT(1) NOT NULL,
    lost TINYINT(1) NOT NULL,
    good TINYINT(1) NOT NULL,
    diverted TINYINT(1) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cart destination mapping
CREATE TABLE PRTCarts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barcode VARCHAR(10) NOT NULL UNIQUE,
    destination INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Cart removal requests
CREATE TABLE PRTRemoveCart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barcode VARCHAR(10) NOT NULL,
    area INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SAMPLE DATA
-- ============================================================================

-- Sample cart destinations (barcodes 0001-0010)
INSERT INTO PRTCarts (barcode, destination) VALUES
    ('0001', 1), ('0002', 2), ('0003', 3), ('0004', 4), ('0005', 1),
    ('0006', 2), ('0007', 3), ('0008', 4), ('0009', 1), ('0010', 2);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT '=== Setup Complete ===' AS status;
SHOW TABLES;

SELECT 'PRTCarts sample data:' AS info;
SELECT * FROM PRTCarts;
