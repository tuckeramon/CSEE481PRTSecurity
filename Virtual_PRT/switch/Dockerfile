FROM alpine:3.19

# Install basic networking tools
RUN apk add --no-cache \
    dropbear \
    lighttpd \
    curl \
    wget \
    iproute2

# Ports: SSH (22), Web (80)
EXPOSE 22 80

# TODO: Add your network monitoring/management tools here
# See README.md for examples

CMD ["/bin/sh", "-c", "echo 'Switch container ready' && tail -f /dev/null"]