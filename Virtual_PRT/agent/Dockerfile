# Import Kali
FROM kalilinux/kali-rolling

# Update and Install tools
RUN apt update && apt -y install \
    kali-linux-headless \
    python3-pip \
    python3-nmap \
    iproute2 \
    && apt clean

# Install Python libraries for LLM communication and ICS testing
RUN pip3 install --no-cache-dir \
    requests \
    pymodbus \
    scapy

# Add workspace and import agent scripts
WORKDIR /home/agent
COPY ./scripts /home/agent/scripts

# Run as a non-root user cuz i think thats safe idk.
RUN useradd -m red-team
USER red-team

CMD ["/bin/bash"]
