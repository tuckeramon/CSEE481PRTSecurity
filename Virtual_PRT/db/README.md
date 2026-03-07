# Database Container

## Base Image
- `mysql:8.0.42`

## Environment Variables
- MYSQL_ROOT_PASSWORD: password
- MYSQL_DATABASE: prt_system

## Ports
- 3306: MySQL

## Current Schema
Basic tables:
- stations
- vehicles
- security_events

## TODO
- [ ] Add custom tables for your PRT system
- [ ] Create stored procedures
- [ ] Add triggers for automatic logging
- [ ] Set up users and permissions

## Customization
Edit `init.sql` to:
- Add/modify tables
- Insert initial data
- Create views
- Add indexes