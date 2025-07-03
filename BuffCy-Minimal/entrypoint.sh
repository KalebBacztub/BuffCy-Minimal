#!/bin/sh
set -e
# This script receives the target binary name as an argument from docker-compose
# and passes it to the GDB server, which is the container's main process.
exec python3 gdb_mcp_server.py "$1"
