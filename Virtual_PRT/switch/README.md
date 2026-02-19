# Switch Container

## Base Image
- `alpine:3.19`

## Installed Tools
- dropbear (SSH)
- lighttpd (web)
- curl/wget
- iproute2

## Ports
- 22: SSH
- 80: Web

## TODO
- [ ] Add SNMP monitoring
- [ ] Configure VLANs
- [ ] Add network traffic monitoring
- [ ] Set up alerting

## Customization
Edit Dockerfile to add:
- SNMP tools
- Network monitoring scripts
- Custom configuration