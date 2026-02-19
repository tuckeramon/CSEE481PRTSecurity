# Red Team Container

## Base Image
- `kalilinux/kali-rolling:latest`

## Installed Tools
- nmap
- curl/wget
- (Kali comes with many tools pre-installed)

## Ports
- 8000: Attack framework web interface

## TODO
- [ ] Install ICS-specific tools (pymodbus, etc.)
- [ ] Add attack scripts for PLC/HMI
- [ ] Configure reconnaissance tools
- [ ] Set up exploitation framework

## Customization
Edit Dockerfile to:
- Install Python ICS libraries
- Add custom attack scripts
- Configure Metasploit
- Add MITRE ATT&CK tools