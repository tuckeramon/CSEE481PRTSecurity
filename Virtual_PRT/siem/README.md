# SIEM Container

## Base Image
- `ubuntu:22.04`

## Installed Tools
- Python 3
- curl/wget
- Basic utilities

## Ports
- 1514: Syslog
- 55000: API
- 9200: Elasticsearch

## TODO
- [ ] Install Wazuh or ELK stack
- [ ] Configure log collection
- [ ] Set up ICS protocol monitoring
- [ ] Create detection rules
- [ ] Configure alerting

## Customization
Edit Dockerfile to:
- Install Wazuh/ELK
- Add ICS monitoring scripts
- Configure log parsing