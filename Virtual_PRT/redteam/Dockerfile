FROM kalilinux/kali-rolling:latest

# Install basic tools (Kali comes with many pre-installed)
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    nmap \
    python3 \
    python3-pip \
    metasploit-framework \
    && rm -rf /var/lib/apt/lists/*

# Port for attack framework web interface
EXPOSE 8000

# TODO: Add your ICS-specific attack tools here
# See README.md for tool recommendations

CMD ["/bin/bash", "-c", "echo 'Red Team container ready' && tail -f /dev/null"]
