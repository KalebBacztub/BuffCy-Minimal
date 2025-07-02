#!/bin/sh
set -e
# This script receives the target binary name as an argument from docker-compose
exec python3 gdb_mcp_server.py "$1"