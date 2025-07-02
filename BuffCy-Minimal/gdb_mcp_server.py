# gdb_mcp_server.py
import socket
import json
from pygdbmi.gdbcontroller import GdbController
import sys
import os # Import os to read environment variables

class GDBManager:
    """Manages a single GDB session for one exploit attempt."""
    def __init__(self, program_path):
        print(f"[GDB MANAGER] Initializing new GDB session...")
        gdb_args = ["--args", program_path, "--nodaemon"]
        self.gdbmi = GdbController(gdb_args=gdb_args)
        print(f"[GDB MANAGER] Session started for {program_path} with args: --nodaemon")

    def run_and_get_crash(self):
        print("[GDB MANAGER] Sending -exec-run and waiting for event...")
        output = self.gdbmi.write('-exec-run', timeout_sec=20)
        print(f"[GDB-MI RAW OUTPUT for -exec-run]: {output}")
        
        is_crash = any("SIGSEGV" in item.get('payload', {}).get('signal-name', '') for item in output)
        
        if is_crash:
            print("[GDB MANAGER] SIGSEGV detected!")
            reg_output = self.gdbmi.write('-data-list-register-values x eip esp')
            return {'status': 'crashed', 'registers': self._parse_registers(reg_output)}
        
        return {'status': 'no_crash', 'raw_output': output}

    def _parse_registers(self, gdb_output):
        regs = {}
        if not gdb_output: return regs
        for record in gdb_output:
            if record.get('message') == 'done' and 'register-values' in record.get('payload', {}):
                for reg in record['payload']['register-values']:
                    regs[reg['name']] = reg['value']
                return regs
        return regs

    def close(self):
        self.gdbmi.exit()
        print("[GDB MANAGER] Session terminated.")

def main_server_loop(program_path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 8080))
        s.listen()
        print(f"[SERVER] GDB MCP Server listening on 0.0.0.0:8080")
        conn, addr = s.accept()
        with conn:
            print(f"[SERVER] Agent connected from {addr}")
            data = conn.recv(4096)
            if data:
                command = json.loads(data.decode().strip())
                if command.get('method') == 'run_and_get_crash_info':
                    gdb_manager = GDBManager(program_path)
                    response = gdb_manager.run_and_get_crash()
                    gdb_manager.close()
                    print(f"[SERVER] Sending response: {response}")
                    conn.sendall(json.dumps(response).encode() + b'\n')

if __name__ == "__main__":
    # The entrypoint script will now pass the binary name
    target_binary = os.getenv("TARGET_BINARY")
    if not target_binary:
        print("[SERVER] FATAL: TARGET_BINARY environment variable not set.")
        sys.exit(1)
    
    main_server_loop(f"./{target_binary}")