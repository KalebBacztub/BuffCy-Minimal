# gdb_mcp_server.py
import socket
import json
from pygdbmi.gdbcontroller import GdbController
import sys

class GDBManager:
    def __init__(self, program_path):
        print(f"[GDB MANAGER] Initializing new GDB session...")
        self.gdbmi = GdbController()
        self.gdbmi.write(f'-file-exec-and-symbols {program_path}', timeout_sec=5)
        self.gdbmi.write('-exec-set-args --nodaemon', timeout_sec=5)
        print(f"[GDB MANAGER] Session started for {program_path} with args: --nodaemon")

    def start_non_blocking(self):
        """Starts the program and returns immediately."""
        print("[GDB MANAGER] Sending -exec-run...")
        # FIX: Added '&' to run the GDB command in the background.
        # This breaks the deadlock by allowing the write() call to return immediately.
        self.gdbmi.write('-exec-run &')
        return {'status': 'running'}

    def _is_crash_event(self, item):
        if not isinstance(item, dict): return False
        payload = item.get('payload')
        if not isinstance(payload, dict): return False
        return "SIGSEGV" in payload.get('signal-name', '')

    def check_for_crash(self):
        """Checks the GDB MI output for a crash event."""
        print("[GDB MANAGER] Checking for crash event...")
        output = self.gdbmi.get_gdb_response(timeout_sec=1, raise_error_on_timeout=False) # Reduced timeout for quicker polling

        if any(self._is_crash_event(item) for item in output):
            print("[GDB MANAGER] SIGSEGV detected!")
            # Request specific registers EIP (for 32-bit) / RIP (for 64-bit)
            # The prompt asks for EIP, assuming 32-bit context.
            # If target is 64-bit, this should be 'rip'
            reg_output = self.gdbmi.write('-data-list-register-values x eip esp') 
            return {'status': 'crashed', 'registers': self._parse_registers(reg_output)}

        print("[GDB MANAGER] No crash detected.")
        return {'status': 'no_crash'}

    def close(self):
        self.gdbmi.exit()
        print("[GDB MANAGER] Session terminated.")

def main_server_loop(program_path):
    gdb_manager = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', 8080))
            s.listen()
            print(f"[SERVER] GDB MCP Server listening on 0.0.0.0:8080")
            conn, addr = s.accept()
            with conn:
                print(f"[SERVER] Agent connected from {addr}")
                gdb_manager = GDBManager(program_path)

                while True: # Keep listening for commands
                    data = conn.recv(4096)
                    if not data:
                        break # Agent disconnected

                    command = json.loads(data.decode().strip())
                    method = command.get('method')
                    print(f"[SERVER] Received command: {method}")

                    if method == 'start_non_blocking':
                        response = gdb_manager.start_non_blocking()
                        conn.sendall(json.dumps(response).encode() + b'\n')
                    elif method == 'check_for_crash':
                        response = gdb_manager.check_for_crash()
                        conn.sendall(json.dumps(response).encode() + b'\n')
                        # Removed the 'break' here to keep the server alive for multiple checks
                    else:
                        conn.sendall(json.dumps({'error': 'unknown_method'}).encode() + b'\n')
    finally:
        if gdb_manager:
            gdb_manager.close()
        print("[SERVER] Connection closed and GDB session terminated.")


if __name__ == "__main__":
    if len(sys.argv) < 2 or not sys.argv[1]:
        print("[SERVER] FATAL: No program path provided.")
        sys.exit(1)

    program_path_arg = sys.argv[1].replace("--nodaemon", "").strip()
    main_server_loop(program_path_arg)