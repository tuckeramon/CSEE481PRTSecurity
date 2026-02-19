# PLC Container

## Base Image
- `fdamador/openplc:latest`

## Ports
- 502: Modbus TCP
- 44818: EtherNet/IP
- 8080: Web interface

## TODO
- [ ] Add ladder logic programs to /opt/openplc/programs/
- [ ] Configure PLC registers
- [ ] Set up Modbus/EtherNet/IP communication

## Customization
Edit the Dockerfile to add:
- Ladder logic files
- Custom runtime configuration
- Additional Python scripts for PLC communication