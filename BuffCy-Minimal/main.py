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
    # ... (same as before)
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.sock, self.buffer = None, b""
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for i in range(15):
            try:
                self.sock.connect((self.host, self.port)); print("[AGENT] Connected."); return
            except ConnectionRefusedError: time.sleep(1)
        raise ConnectionRefusedError("Could not connect to GDB server.")
    def send_command(self, method, params=None):
        if not self.sock: self.connect()
        request = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
        self.sock.sendall(json.dumps(request).encode() + b'\n')
        while b'\n' not in self.buffer: self.buffer += self.sock.recv(4096)
        message_data, self.buffer = self.buffer.split(b'\n', 1)
        return json.loads(message_data.decode())
    def close(self):
        if self.sock: self.sock.close()

def main(target_binary: str):
    print(f"***** AGENT STARTING EXPLOIT RUN AGAINST: {target_binary} *****")
    agent = ExploitAgent(model_name="openai/gpt-4o")
    gdb_client = GDBClient(TARGET_HOST, TARGET_PORT)
    try:
        print("\n--- 🚀 PHASE 1: Finding EIP Offset ---")
        gdb_client.connect()
        pattern = agent.generate_cyclic_pattern(1200)
        
        container_name = f"buffcyminimal-{target_binary}-1" # Predict container name
        trigger_command = ["docker", "exec", container_name, "python3", "exploit_trigger.py", "--payload", pattern]
        subprocess.Popen(trigger_command)
        time.sleep(2)
        
        crash_info = gdb_client.send_command('run_and_get_crash_info')
        if crash_info.get("status") == "crashed":
            offset = agent.analyze_crash_and_get_offset(crash_info, len(pattern))
            print(f"--- ✅ SUCCESS: Agent determined offset is: {offset} ---")
        else:
            print(f"--- ❌ FAILED: Program did not crash as expected. ---")
    finally:
        gdb_client.close()
        print("\n🎉 Exploit sequence finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    main(args.target)