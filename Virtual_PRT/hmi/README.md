# HMI Container

## Base Image
- `python:3.11-slim`

## Framework
- Flask 3.0.0

## Ports
- 8080: Web dashboard

## Current Features
- Basic Flask "Hello World" app
- API endpoint at /api/status

## TODO
- [ ] Connect to PLC (Modbus/EtherNet/IP)
- [ ] Connect to database
- [ ] Create dashboard UI
- [ ] Add real-time updates
- [ ] Implement control buttons

## Customization
Edit `app.py` to:
- Add routes for your dashboard
- Connect to PLC using pymodbus
- Query database for status
- Create HTML templates