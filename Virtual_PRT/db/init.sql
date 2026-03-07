-- Basic PRT Database Skeleton
-- Add your custom tables here

CREATE DATABASE IF NOT EXISTS prt_system;
USE prt_system;

-- Example: Stations table
CREATE TABLE IF NOT EXISTS stations (
    station_id INT PRIMARY KEY AUTO_INCREMENT,
    station_name VARCHAR(100),
    position_meters DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'active'
);

-- Example: Vehicles table  
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INT PRIMARY KEY AUTO_INCREMENT,
    vehicle_name VARCHAR(100),
    current_position DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'idle'
);

-- Example: Security events table
CREATE TABLE IF NOT EXISTS security_events (
    event_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(50),
    description TEXT
);

-- Insert sample data
INSERT INTO stations (station_name, position_meters) VALUES
('Terminal A', 0),
('Terminal B', 500),
('Terminal C', 1000);

INSERT INTO vehicles (vehicle_name, current_position, status) VALUES
('PRT-001', 0, 'idle'),
('PRT-002', 500, 'idle');

-- TODO: Add your custom tables below
-- CREATE TABLE your_custom_table (...);