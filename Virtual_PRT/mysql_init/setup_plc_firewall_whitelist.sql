/*
 * SQL Setup Script for PLC Firewall Whitelist
 *
 * Creates the PLCFirewallWhitelist table for dynamic IP management.
 *
 * Run after setup_plc_security_alerts.sql:
 *   mysql -u root -p prt_unified < setup_plc_firewall_whitelist.sql
 */

USE prt_unified;

CREATE TABLE IF NOT EXISTS PLCFirewallWhitelist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200) DEFAULT NULL,
    added_by VARCHAR(100) DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ip_active (ip_address, is_active)
);

-- Insert default whitelist entries
INSERT IGNORE INTO PLCFirewallWhitelist (ip_address, description, added_by) VALUES
    ('127.0.0.1', 'Localhost - backend application', 'system'),
    ('192.168.1.70', 'HMI - SCADALTs', 'system'),
    ('192.168.1.30', 'MySQL Database Server', 'system'),
    ('192.168.1.20', 'Blue Team SIEM', 'system');
