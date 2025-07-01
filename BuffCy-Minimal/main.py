# main.py
import os
import time
import json
import socket
import subprocess
from dotenv import load_dotenv
from agent import ExploitAgent

# Load .env file to get TARGET_BINARY for logging, etc.
load_dotenv()

TARGET_HOST = 'target'
TARGET_PORT = 8080

# GDBClient class remains the same...
class GDBClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for _ in range(10):
            try:
                self.sock.connect((self.host, self.port))
                print("Connected to GDB MCP Server.")
                return
            except ConnectionRefusedError:
                time.sleep(1)
        raise ConnectionRefusedError("Could not connect to GDB server.")

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

def main():
    target_binary_name = os.getenv("TARGET_BINARY", "unknown_target")
    aslr_setting = os.getenv("ASLR_SETTING", "2")
    aslr_mode = "on" if aslr_setting == "2" else "off"

    print(f"***** AGENT STARTING EXPLOIT AGAINST: {target_binary_name} (ASLR: {aslr_mode.upper()}) *****")

    agent = ExploitAgent(model_name="openai/gpt-4o")
    gdb_client = GDBClient(TARGET_HOST, TARGET_PORT)

    try:
        gdb_client.connect()
        # Your exploit logic phases (find offset, get shell, etc.) go here.
        # For now, we'll just confirm the connection and exit.
        print("\n--- Agent is connected and ready. ---")
        time.sleep(2)

    except Exception as e:
        print(f"An error occurred during the exploit run: {e}")
    finally:
        gdb_client.close()
        print("\n🎉 Exploit sequence finished.")

if __name__ == "__main__":
    main()