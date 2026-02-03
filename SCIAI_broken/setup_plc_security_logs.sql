/*
 * SQL Setup Script for PLC Security Logging
 *
 * Creates the PLCSecurityLogs table in the prt_unified database
 * for tracking security-relevant events from Rockwell Logix PLCs.
 *
 * Security Events Tracked:
 *   - Controller faults (major/minor faults from PLC)
 *   - Mode changes (Run/Program/Remote transitions)
 *   - Connection events (new connections, disconnections)
 *   - Controller status snapshots (periodic health checks)
 *   - Configuration changes (firmware, keyswitch position)
 *
 * Run this script after setup_unified_database.sql:
 *   mysql -u root -p prt_unified < setup_plc_security_logs.sql
 */

USE prt_unified;

-- ============================================================================
-- PLC SECURITY LOGS TABLE
-- Stores security and diagnostic events from Rockwell Logix PLCs
-- ============================================================================

CREATE TABLE IF NOT EXISTS PLCSecurityLogs (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- PLC Identification
    plc_ip VARCHAR(50) NOT NULL,              -- IP address of PLC
    plc_name VARCHAR(100) DEFAULT NULL,       -- Controller name (from PLC)
    plc_serial VARCHAR(50) DEFAULT NULL,      -- Serial number for device verification

    -- Event Classification
    event_type VARCHAR(50) NOT NULL,          -- Type: FAULT, MODE_CHANGE, CONNECTION, STATUS, CONFIG_CHANGE
    severity VARCHAR(20) NOT NULL DEFAULT 'INFO',  -- INFO, WARNING, ERROR, CRITICAL

    -- Event Details
    event_code VARCHAR(50) DEFAULT NULL,      -- Fault code or event identifier
    event_message VARCHAR(500) NOT NULL,      -- Human-readable description

    -- Context Data (JSON for flexibility)
    previous_state VARCHAR(100) DEFAULT NULL, -- Previous state (for change events)
    current_state VARCHAR(100) DEFAULT NULL,  -- Current state
    raw_data TEXT DEFAULT NULL,               -- Raw PLC data as JSON

    -- Timestamps
    plc_timestamp DATETIME DEFAULT NULL,      -- Timestamp from PLC (if available)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When log was recorded

    -- Indexes for efficient querying
    INDEX idx_plc_ip (plc_ip),
    INDEX idx_event_type (event_type),
    INDEX idx_severity (severity),
    INDEX idx_timestamp (timestamp),
    INDEX idx_plc_serial (plc_serial)
);

-- ============================================================================
-- PLC BASELINE TABLE
-- Stores expected/baseline configuration for security comparison
-- Used to detect unauthorized changes to PLC configuration
-- ============================================================================

CREATE TABLE IF NOT EXISTS PLCBaseline (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plc_ip VARCHAR(50) NOT NULL UNIQUE,       -- IP address (one baseline per PLC)
    plc_name VARCHAR(100) DEFAULT NULL,       -- Expected controller name
    plc_serial VARCHAR(50) DEFAULT NULL,      -- Expected serial number
    firmware_version VARCHAR(50) DEFAULT NULL,-- Expected firmware revision
    product_type VARCHAR(100) DEFAULT NULL,   -- Expected product type
    expected_mode VARCHAR(20) DEFAULT 'Run',  -- Expected operating mode
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'PLC Security Logging tables created!' AS message;
SHOW TABLES LIKE 'PLC%';

-- Show table structure
DESCRIBE PLCSecurityLogs;
DESCRIBE PLCBaseline;
