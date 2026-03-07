# 🎉 PRT Security Simulation - SKELETON COMPLETE!

## ✅ Status: ALL SYSTEMS OPERATIONAL

All 6 containers are running successfully with minimal, working configurations.

---

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Stop all
docker-compose down
```

---

## 📊 Running Services

| Service | Container | IP Address | Ports | Status |
|---------|-----------|------------|-------|--------|
| **PLC** | ab_plc_51 | 192.168.1.51 | 502, 44818, 8081 | ✅ Running |
| **Database** | mgt_db_30 | 192.168.1.30 | 3306 | ✅ Running |
| **HMI** | ab_hmi_70 | 192.168.1.70 | 8080 | ✅ Running |
| **Switch** | schneider_switch_200 | 192.168.1.200 | 2222, 8082 | ✅ Running |
| **SIEM** | blue_team_siem | 192.168.1.20 | 1514, 55000, 9200 | ✅ Running |
| **Red Team** | red_team_beachhead | 192.168.1.10 | 8000 | ✅ Running |

---

## 🌐 Access URLs

- **HMI Dashboard**: http://localhost:8080 ✅ Tested
- **PLC Web**: http://localhost:8081 ✅ Tested  
- **Database**: mysql://192.168.1.30:3306 ✅ Tested
- **Switch Web**: http://localhost:8082
- **Switch SSH**: ssh://localhost:2222

---

## 📁 Project Structure

```
Virtual_PRT/
├── docker-compose.yaml      # Orchestration
├── README.md                # This file
├── db/
│   ├── Dockerfile          # MySQL 8.0
│   ├── init.sql            # Basic PRT schema
│   └── README.md           # Database customization guide
├── plc/
│   ├── Dockerfile          # OpenPLC
│   └── README.md           # PLC customization guide
├── hmi/
│   ├── Dockerfile          # Python Flask
│   ├── app.py              # Hello World dashboard
│   ├── requirements.txt    # Flask dependencies
│   └── README.md           # HMI customization guide
├── switch/
│   ├── Dockerfile          # Alpine Linux
│   └── README.md           # Switch customization guide
├── siem/
│   ├── Dockerfile          # Ubuntu base
│   └── README.md           # SIEM customization guide
└── redteam/
    ├── Dockerfile          # Kali Linux
    └── README.md           # Attack tools guide
```

---

## 🎯 Next Steps - Customize Each Component

### 1. Database (`./db/`)
**Current**: Basic stations, vehicles, security_events tables

**Customize**:
```bash
docker exec -it mgt_db_30 mysql -u root -ppassword
# Add your tables and data
```

Or edit `db/init.sql` and rebuild:
```bash
docker-compose up --build db_server -d
```

---

### 2. PLC (`./plc/`)
**Current**: OpenPLC running with web interface

**Customize**:
```bash
# Access PLC web interface
curl http://localhost:8081

# Or enter container to add ladder logic
docker exec -it ab_plc_51 bash
# Add programs to /opt/openplc/programs/
```

---

### 3. HMI (`./hmi/`)
**Current**: Flask "Hello World" app

**Customize**:
Edit `hmi/app.py`:
```python
# Add PLC communication (pymodbus)
# Add database queries
# Create dashboard HTML
```

Then rebuild:
```bash
docker-compose up --build panelview-hmi -d
```

---

### 4. Switch (`./switch/`)
**Current**: Alpine with SSH and web server

**Customize**:
```bash
docker exec -it schneider_switch_200 sh
# Add SNMP, monitoring tools, etc.
```

Or edit `switch/Dockerfile` to install packages.

---

### 5. SIEM (`./siem/`)
**Current**: Ubuntu base container

**Customize**:
Edit `siem/Dockerfile`:
```dockerfile
# Install Wazuh or ELK stack
# Add ICS monitoring scripts
```

---

### 6. Red Team (`./redteam/`)
**Current**: Kali Linux base with nmap

**Customize**:
```bash
docker exec -it red_team_beachhead bash
# Install ICS tools: apt-get install -y python3-pip
# pip3 install pymodbus scapy
# Add attack scripts
```

---

## 🧪 Testing Commands

```bash
# Test HMI
curl http://localhost:8080

# Test PLC web
curl http://localhost:8081

# Test database
docker exec mgt_db_30 mysql -u root -ppassword -e "SELECT 1;"

# Test all containers
docker-compose ps

# View logs
docker-compose logs -f
```

---

## 🔧 Troubleshooting

**Container won't start**:
```bash
docker-compose logs [service_name]
```

**Rebuild single service**:
```bash
docker-compose up --build [service_name] -d
```

**Enter container**:
```bash
docker exec -it [container_name] bash  # or sh for Alpine
```

**Check network**:
```bash
docker network ls
docker network inspect virtual_prt_simulation_lan
```

---

## 📚 Documentation

Each component has a `README.md` with specific customization instructions.

---

## ✨ What's Included

✅ **Working base images** for all 6 components  
✅ **Network connectivity** on 192.168.1.0/24  
✅ **Basic database schema** with sample data  
✅ **Minimal Flask app** as HMI starting point  
✅ **OpenPLC runtime** ready for ladder logic  
✅ **Placeholder READMEs** for each component  

---

## 🎓 Your Next Steps

1. **Explore each container**: `docker exec -it [name] bash`
2. **Read the READMEs** in each directory
3. **Add your PRT-specific features**
4. **Test modifications** with `docker-compose up --build -d`
5. **Document your changes**

---

**Project Status**: ✅ **SKELETON COMPLETE - READY FOR CUSTOMIZATION**