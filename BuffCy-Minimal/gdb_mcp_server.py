import socket
import json
from pygdbmi.gdbcontroller import GdbController
import sys

class GDBManager:
    def __init__(self, program_path):
        gdb_args = ["--args", program_path, "--nodaemon"]
        self.gdbmi = GdbController(gdb_args=gdb_args)
        print(f"[GDB MANAGER] Session started for {program_path}")

    def run_and_get_crash(self):
        output = self.gdbmi.write('-exec-run', timeout_sec=20)
        is_crash = any("SIGSEGV" in str(item) for item in output)
        if is_crash:
            reg_output = self.gdbmi.write('-data-list-register-values x eip esp')
            return {'status': 'crashed', 'registers': self._parse_registers(reg_output)}
        return {'status': 'no_crash'}

    def _parse_registers(self, gdb_output):
        # ... (same as before)
        regs = {}
        for record in gdb_output:
            if record.get('message') == 'done' and 'register-values' in record.get('payload', {}):
                for reg in record['payload']['register-values']: regs[reg['name']] = reg['value']
                return regs
        return regs
    
    def close(self): self.gdbmi.exit()

def main_server_loop(program_path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 8080))
        s.listen()
        print(f"[SERVER] Listening...")
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
                    conn.sendall(json.dumps(response).encode() + b'\n')

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    main_server_loop(sys.argv[1])