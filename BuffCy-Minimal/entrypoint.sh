#!/bin/sh
set -e

echo "Setting ASLR to: ${ASLR_SETTING}"
echo "${ASLR_SETTING}" > /proc/sys/kernel/randomize_va_space
echo "ASLR is now:"
cat /proc/sys/kernel/randomize_va_space

echo "Starting GDB server for target: ./${TARGET_BINARY}"

# Correctly pass the target binary as an argument to the python script
exec python3 gdb_mcp_server.py "./${TARGET_BINARY}"