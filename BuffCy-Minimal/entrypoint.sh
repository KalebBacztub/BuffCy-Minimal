#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Use the ASLR_SETTING environment variable passed from docker-compose
echo "Setting ASLR to: ${ASLR_SETTING}"
echo "${ASLR_SETTING}" > /proc/sys/kernel/randomize_va_space
echo "ASLR is now:"
cat /proc/sys/kernel/randomize_va_space

# The TARGET_BINARY variable will also be passed from docker-compose
echo "Starting GDB server for target: ./${TARGET_BINARY}"

# Execute the GDB server, replacing this shell process
exec python3 gdb_mcp_server.py