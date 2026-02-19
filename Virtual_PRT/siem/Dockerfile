FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install basic tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Ports for SIEM services
EXPOSE 1514 1515 55000 9200

# TODO: Add Wazuh or your preferred SIEM stack here
# See README.md for installation instructions

CMD ["/bin/bash", "-c", "echo 'SIEM container ready' && tail -f /dev/null"]