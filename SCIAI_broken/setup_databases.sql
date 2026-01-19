/*
 * SQL Setup Script for PRT Industrial Logging System
 *
 * This script creates and initializes two databases:
 *   1. prtdb - Backend database for PLC communication and sorter data
 *   2. prt_system - Frontend database for user authentication and activity logs
 *
 * Run this script in MySQL Workbench or via command line:
 *   mysql -u root -p < setup_databases.sql
 *
 * Created to fix missing database schema in the codebase
 */

-- ============================================================================
-- BACKEND DATABASE: prtdb
-- Used by the back-end server to log PLC (Programmable Logic Controller) data
-- ============================================================================

-- Create the back-end database if it doesn't exist
CREATE DATABASE IF NOT EXISTS prtdb;
USE prtdb;

-- Table for sorter requests
-- Logs incoming requests from the PLC when a cart needs routing information
CREATE TABLE IF NOT EXISTS PRTSorterRequest (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- Unique identifier for each request
    sorterID INT NOT NULL,                    -- Which sorter (1 or 2) made the request
    transactionID INT NOT NULL,               -- Transaction ID from the PLC for tracking
    barcode VARCHAR(10) NOT NULL,             -- Cart barcode (e.g., "0001", "0002")
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- When the request was received
);

-- Table for sorter responses
-- Logs responses sent back to the PLC with routing destinations
CREATE TABLE IF NOT EXISTS PRTSorterResponse (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- Unique identifier for each response
    sorterID INT NOT NULL,                    -- Which sorter received the response
    barcode VARCHAR(10) NOT NULL,             -- Cart barcode being routed
    transactionID INT NOT NULL,               -- Matching transaction ID from request
    destination INT NOT NULL,                 -- Destination station (1-4) assigned
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- When the response was sent
);

-- Table for sorter reports
-- Logs status reports from the PLC about cart processing results
CREATE TABLE IF NOT EXISTS PRTSorterReport (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- Unique identifier for each report
    sorterID INT NOT NULL,                    -- Which sorter processed the cart
    barcode VARCHAR(10) NOT NULL,             -- Cart barcode that was processed
    active TINYINT(1) NOT NULL,               -- Flag: cart is active in system
    lost TINYINT(1) NOT NULL,                 -- Flag: cart was lost during processing
    good TINYINT(1) NOT NULL,                 -- Flag: cart successfully processed
    diverted TINYINT(1) NOT NULL,             -- Flag: cart was diverted to destination
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- When the report was received
);

-- Table for cart destination mapping
-- Stores which station each cart should be routed to (master routing table)
CREATE TABLE IF NOT EXISTS PRTCarts (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- Unique identifier
    barcode VARCHAR(10) NOT NULL UNIQUE,      -- Cart barcode (must be unique)
    destination INT NOT NULL,                 -- Target station (1-4)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,     -- When cart was added
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  -- Last update time
);

-- Table for cart removal requests
-- Logs when operators request a cart to be removed from the system
CREATE TABLE IF NOT EXISTS PRTRemoveCart (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- Unique identifier
    barcode VARCHAR(10) NOT NULL,             -- Cart barcode to remove
    area INT NOT NULL,                        -- Area/zone where cart should be removed
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- When removal was requested
);

-- Insert sample cart data for testing
-- This creates 10 test carts with barcodes 0001-0010 mapped to stations 1-4
-- ON DUPLICATE KEY prevents errors if running the script multiple times
INSERT INTO PRTCarts (barcode, destination) VALUES
    ('0001', 1),  -- Cart 0001 routes to Station 1
    ('0002', 2),  -- Cart 0002 routes to Station 2
    ('0003', 3),  -- Cart 0003 routes to Station 3
    ('0004', 4),  -- Cart 0004 routes to Station 4
    ('0005', 1),  -- Cart 0005 routes to Station 1
    ('0006', 2),  -- Cart 0006 routes to Station 2
    ('0007', 3),  -- Cart 0007 routes to Station 3
    ('0008', 4),  -- Cart 0008 routes to Station 4
    ('0009', 1),  -- Cart 0009 routes to Station 1
    ('0010', 2)   -- Cart 0010 routes to Station 2
ON DUPLICATE KEY UPDATE destination=VALUES(destination);  -- Update if already exists

-- ============================================================================
-- FRONTEND DATABASE: prt_system
-- Used by the front-end GUI for user authentication and activity logging
-- ============================================================================

-- Create the front-end database if it doesn't exist
CREATE DATABASE IF NOT EXISTS prt_system;
USE prt_system;

-- Table for user authentication
-- Stores user accounts for GUI login (passwords are hashed with bcrypt)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- Unique user ID
    username VARCHAR(50) NOT NULL UNIQUE,     -- Username (must be unique)
    password_hash VARCHAR(255) NOT NULL,      -- Hashed password (never store plain text!)
    role VARCHAR(20) DEFAULT 'user',          -- User role (user/admin)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Account creation time
);

-- Table for cart activity logs
-- Records all cart movements and events for the front-end activity viewer
CREATE TABLE IF NOT EXISTS cart_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- Unique log entry ID
    cart_id INT NOT NULL,                     -- Cart identifier
    position VARCHAR(50) NOT NULL,            -- Location (Station_1, Segment_A, etc.)
    event VARCHAR(100) NOT NULL,              -- Event description (Active, Idle, etc.)
    action_type VARCHAR(50) DEFAULT NULL,     -- Action type (Request, Response, etc.)
    time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When event occurred
    INDEX idx_cart_id (cart_id),              -- Index for fast cart lookup
    INDEX idx_time_stamp (time_stamp)         -- Index for time-based queries
);

-- Insert sample activity log data for testing
-- Creates a few test log entries showing different cart states and positions
INSERT INTO cart_logs (cart_id, position, event, action_type) VALUES
    (1, 'Station_1', 'Active', 'Request'),     -- Cart 1 active at Station 1
    (2, 'Station_2', 'Idle', 'Response'),      -- Cart 2 idle at Station 2
    (3, 'Station_3', 'Active', 'Request'),     -- Cart 3 active at Station 3
    (4, 'Station_4', 'Idle', 'Response'),      -- Cart 4 idle at Station 4
    (5, 'Segment_A', 'Active', 'Request');     -- Cart 5 active in Segment A

-- ============================================================================
-- VERIFICATION SECTION
-- Display summary of what was created to confirm successful setup
-- ============================================================================

SELECT 'Database setup complete!' AS message;

-- Show all tables in prtdb database
SELECT 'prtdb tables created:' AS info;
USE prtdb;
SHOW TABLES;

-- Show all tables in prt_system database
SELECT 'prt_system tables created:' AS info;
USE prt_system;
SHOW TABLES;
