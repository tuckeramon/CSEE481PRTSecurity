FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    libxcb1 \
    libx11-6 \
    libgl1 \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    net-tools \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000 5900

CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & sleep 2 && x11vnc -display :99 -forever -shared & sleep 1 && python /app/src/front-end/api_server.py"]