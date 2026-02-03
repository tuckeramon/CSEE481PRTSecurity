# Wazuh SIEM Integration for PLC Security Monitoring

## Overview

This guide explains how to integrate the PLC Security Monitor with Wazuh, an open-source SIEM (Security Information and Event Management) platform. This setup demonstrates real-world industrial control system (ICS) security monitoring.

## Architecture

```
┌─────────────────┐
│  Rockwell PLC   │
│  (Logix5318ER)  │
└────────┬────────┘
         │ EtherNet/IP (pycomm3)
         ▼
┌─────────────────────────────────────────────────┐
│           PLCSecurityMonitor                     │
│                                                  │
│  Detects: Mode changes, Faults, Baseline issues │
└────────────────┬────────────────┬───────────────┘
                 │                │
         ┌───────┴───────┐  ┌─────┴─────┐
         ▼               ▼  ▼           ▼
┌─────────────────┐  ┌──────────────────────┐
│  MySQL Database │  │  JSON Log File       │
│                 │  │  plc_security.json   │
│  - Queries      │  │                      │
│  - Frontend     │  │  Wazuh Agent watches │
│  - History      │  │  this file           │
└─────────────────┘  └──────────┬───────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │    Wazuh Agent      │
                     │  (reads JSON logs)  │
                     └──────────┬──────────┘
                                │ Encrypted (1514/tcp)
                                ▼
                     ┌─────────────────────┐
                     │   Wazuh Manager     │
                     │                     │
                     │  - Rule matching    │
                     │  - Alert generation │
                     │  - Correlation      │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  Wazuh Dashboard    │
                     │  (Kibana/OpenSearch)│
                     │                     │
                     │  - Visualizations   │
                     │  - Alerts           │
                     │  - Investigations   │
                     └─────────────────────┘
```

## Prerequisites

- Windows 10/11 or Linux
- Python 3.8+ with the PLC backend running
- Network access to install Wazuh components

## Quick Start

### Option A: Wazuh Cloud (Easiest for Learning)

1. Sign up for free at: https://console.cloud.wazuh.com/
2. Download and install the Wazuh agent for your OS
3. Configure the agent with your cloud endpoint
4. Add the localfile configuration (see Step 2 below)

### Option B: Local Wazuh Server (Full Control)

Follow the official installation guide:
https://documentation.wazuh.com/current/installation-guide/

## Step-by-Step Setup

### Step 1: Verify PLC Security Logs are Being Generated

First, confirm the JSON logs are being written:

```bash
# Check if log file exists and has content
# Windows PowerShell:
Get-Content ".\SCIAI_broken\back-end\logs\plc_security\plc_security.json" -Tail 10

# Linux:
tail -10 ./SCIAI_broken/back-end/logs/plc_security/plc_security.json
```

You should see JSON lines like:
```json
{"timestamp":"2024-01-15T10:30:45.123456","source":"plc_security","plc_ip":"192.168.1.51","event_type":"STATUS","severity":"INFO","message":"Periodic status: Mode=Run, Faults=No"}
```

### Step 2: Install Wazuh Agent

**Windows:**
```powershell
# Download from Wazuh website
# Run the MSI installer
# During installation, enter your Wazuh manager IP
```

**Linux (Ubuntu/Debian):**
```bash
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | apt-key add -
echo "deb https://packages.wazuh.com/4.x/apt/ stable main" | tee /etc/apt/sources.list.d/wazuh.list
apt-get update
apt-get install wazuh-agent
```

### Step 3: Configure the Agent to Monitor PLC Logs

Edit the agent configuration file:
- **Windows:** `C:\Program Files (x86)\ossec-agent\ossec.conf`
- **Linux:** `/var/ossec/etc/ossec.conf`

Add this block inside `<ossec_config>`:

```xml
<localfile>
  <!-- UPDATE THIS PATH to your actual log location -->
  <location>C:\Users\tucke\Documents\GitHub\CSEE481PRTSecurity\SCIAI_broken\back-end\logs\plc_security\plc_security.json</location>
  <log_format>json</log_format>
  <label key="source_type">plc_security</label>
</localfile>
```

### Step 4: Install Custom Rules on Wazuh Manager

Copy the rules file to the manager:

```bash
# On the Wazuh manager server
sudo cp plc_security_rules.xml /var/ossec/etc/rules/

# Verify rules syntax
sudo /var/ossec/bin/wazuh-analysisd -t

# Restart manager
sudo systemctl restart wazuh-manager
```

### Step 5: Restart the Agent

**Windows:**
```powershell
Restart-Service WazuhSvc
```

**Linux:**
```bash
sudo systemctl restart wazuh-agent
```

### Step 6: Verify Everything Works

1. Generate a test event by running the backend
2. Check the Wazuh dashboard for alerts
3. Look for events with `source: plc_security`

## Understanding the Rules

### Rule Severity Levels

| Level | Meaning | Example Events |
|-------|---------|----------------|
| 1-3 | Low/Informational | Periodic status checks |
| 4-7 | Medium | Minor faults, info events |
| 8-11 | High | Mode changes, config changes |
| 12-15 | Critical | Major faults, device replacement |

### Key Rules to Watch

| Rule ID | What It Detects | Severity |
|---------|-----------------|----------|
| 100021 | PLC entered PROGRAM mode | 12 (Critical) |
| 100022 | Multiple mode changes (attack pattern) | 14 (Critical) |
| 100031 | Major fault on PLC | 14 (Critical) |
| 100042 | Device serial number changed | 15 (Critical) |

## Educational Exercises

### Exercise 1: Trigger a Mode Change Alert

1. If you have PLC access, change the controller mode
2. Or manually add a test event to the log:
   ```bash
   echo '{"timestamp":"2024-01-15T12:00:00","source":"plc_security","plc_ip":"192.168.1.51","event_type":"MODE_CHANGE","severity":"ERROR","message":"Controller mode changed from Run to Program","previous_state":"Run","current_state":"Program"}' >> plc_security.json
   ```
3. Check Wazuh dashboard for the alert

### Exercise 2: Simulate a Brute Force Attack

Add multiple connection failure events:
```bash
for i in {1..6}; do
  echo '{"timestamp":"'$(date -Iseconds)'","source":"plc_security","plc_ip":"192.168.1.51","event_type":"CONNECTION","severity":"ERROR","message":"Failed to connect to PLC"}' >> plc_security.json
  sleep 1
done
```

Watch for rule 100100 to trigger (frequency-based correlation).

### Exercise 3: Create a Custom Rule

1. Edit `plc_security_rules.xml`
2. Add a new rule:
   ```xml
   <rule id="100200" level="10">
     <if_sid>100000</if_sid>
     <match>unauthorized</match>
     <description>Custom: Unauthorized access detected</description>
   </rule>
   ```
3. Reload rules on manager
4. Test with a matching log event

### Exercise 4: Investigate an Alert

1. Find an alert in the Wazuh dashboard
2. Click to expand details
3. Identify:
   - Which rule triggered?
   - What was the raw log data?
   - What PLC was affected?
   - What time did it occur?

## Troubleshooting

### Logs Not Appearing in Wazuh

1. Check agent is running: `systemctl status wazuh-agent`
2. Verify log path is correct in ossec.conf
3. Check agent logs: `/var/ossec/logs/ossec.log`
4. Ensure JSON format is valid (use a JSON validator)

### Rules Not Triggering

1. Verify rules are loaded: `/var/ossec/bin/wazuh-analysisd -t`
2. Check rule syntax in the output
3. Test with `ossec-logtest` tool
4. Ensure `source: plc_security` is in your log events

### Connection Issues

1. Check firewall allows port 1514/tcp
2. Verify agent is registered with manager
3. Check manager IP is correct in agent config

## Files Reference

| File | Purpose |
|------|---------|
| `WazuhLogger.py` | Writes JSON logs for Wazuh |
| `PLCSecurityMonitor.py` | Monitors PLC, dual output |
| `plc_security_rules.xml` | Custom Wazuh rules |
| `ossec_agent_config.xml` | Agent configuration snippet |
| `plc_security.json` | The log file Wazuh monitors |

## Further Learning

- [Wazuh Documentation](https://documentation.wazuh.com/)
- [ICS-CERT Advisories](https://www.cisa.gov/uscert/ics)
- [NIST SP 800-82 (ICS Security)](https://csrc.nist.gov/publications/detail/sp/800-82/rev-2/final)
- [MITRE ATT&CK for ICS](https://attack.mitre.org/techniques/ics/)
