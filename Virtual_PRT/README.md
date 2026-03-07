# PRT Security Simulation - Simplified Skeleton

A minimal Docker-based PRT (Personal Rapid Transit) security testing environment.

## Quick Start

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Stop all
docker-compose down
```

## Components

| Service | IP Address | Ports | Purpose |
|---------|------------|-------|---------|
| PLC | 192.168.1.51 | 502, 44818, 8081 | OpenPLC Controller |
| Database | 192.168.1.30 | 3306 | MySQL with PRT schema |
| HMI | 192.168.1.70 | 8080 | Flask Dashboard |
| Switch | 192.168.1.200 | 2222, 8082 | Network Management |
| SIEM | 192.168.1.20 | 1514, 55000, 9200 | Security Monitoring |
| Red Team | 192.168.1.10 | 8000 | Attack Platform |

## Customize Each Component

### 1. PLC (`./plc/`)
- **Base**: OpenPLC with Modbus/EtherNet/IP
- **Customize**: Add ladder logic to `/opt/openplc/programs/`
- **See**: `plc/README.md`

### 2. Database (`./db/`)
- **Base**: MySQL 8.0 with basic tables
- **Customize**: Edit `init.sql` to add your schema
- **See**: `db/README.md`

### 3. HMI (`./hmi/`)
- **Base**: Flask "Hello World" app
- **Customize**: Edit `app.py` to add dashboard
- **See**: `hmi/README.md`

### 4. Switch (`./switch/`)
- **Base**: Alpine Linux with SSH
- **Customize**: Add SNMP/monitoring tools
- **See**: `switch/README.md`

### 5. SIEM (`./siem/`)
- **Base**: Ubuntu with Python
- **Customize**: Install Wazuh/ELK
- **See**: `siem/README.md`

### 6. Red Team (`./redteam/`)
- **Base**: Kali Linux
- **Customize**: Add ICS attack tools
- **See**: `redteam/README.md`

## Network

All containers communicate on `192.168.1.0/24` subnet.

## Access URLs

- HMI Dashboard: http://localhost:8080
- PLC Web: http://localhost:8081
- Database: mysql://192.168.1.30:3306

## Next Steps

1. Run `docker-compose up -d` to start containers
2. Check each README.md for customization instructions
3. Modify Dockerfiles and configs as needed
4. Rebuild with `docker-compose up --build -d`