#!/bin/bash
set -e

# --- STEP 1: Set ASLR on the Host VM ---
echo "--- 1. Configuring ASLR on the host VM (requires sudo) ---"
# We are hardcoding ASLR off for this test run.
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
echo "ASLR is now: $(cat /proc/sys/kernel/randomize_va_space)"
echo ""

# --- STEP 2: Build and Run Docker Compose ---
echo "--- 2. Building and running the containers ---"
# The --build flag ensures changes are picked up.
docker compose up --build

# --- STEP 3: Cleanup (Optional) ---
echo ""
echo "--- 3. Run finished. Cleaning up containers. ---"
docker compose down