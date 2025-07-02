#!/bin/sh
set -e

# The program path is now the first argument passed to this script
PROGRAM_PATH=$1

if [ -z "$PROGRAM_PATH" ]; then
    echo "[ENTRYPOINT] FATAL: No target binary path provided."
    exit 1
fi

# The ASLR setting is now handled by the docker-compose command
echo "ASLR has been set by Docker."
cat /proc/sys/kernel/randomize_va_space

exec python3 gdb_mcp_server.py "${PROGRAM_PATH}"