#!/bin/bash
set -e

echo "[ENTRYPOINT] Starting D-Bus system daemon..."
mkdir -p /var/run/dbus
# Remove existing pid file if it exists, to ensure clean startup
if [ -f "/run/dbus/pid" ]; then
    echo "[ENTRYPOINT] Removing stale D-Bus pid file..."
    rm /run/dbus/pid
fi
dbus-daemon --system &
sleep 1

echo "[ENTRYPOINT] Engineering Connman environment..."
IFACE="eth0"

if [ ! -d "/sys/class/net/$IFACE" ]; then
    echo "[ENTRYPOINT] FATAL: Network interface '$IFACE' not found."
    exit 1
fi

MAC_ADDR=$(cat /sys/class/net/$IFACE/address | tr '[:lower:]' '[:upper:]' | tr -d ':')
SERVICE_NAME="ethernet_${MAC_ADDR}_cable"

mkdir -p /var/lib/connman

# FIX: Write the static IP of our agent directly into the config file
AGENT_IP="172.20.0.10"
cat > /var/lib/connman/${SERVICE_NAME}.config << EOL
[service_${SERVICE_NAME}]
Type = ethernet
IPv4.method = manual
Address = $(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')/24
Nameservers = ${AGENT_IP}
EOL

echo "[ENTRYPOINT] Pre-created config for service ${SERVICE_NAME} to use DNS ${AGENT_IP}"

echo "[ENTRYPOINT] Executing GDB server..."
exec python3 gdb_mcp_server.py "$@"