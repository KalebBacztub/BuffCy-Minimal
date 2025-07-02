# gdb_mcp_server.py
import socket
import json
from pygdbmi.gdbcontroller import GdbController
import sys
import subprocess

class GDBServer:
    def __init__(self, program_path):
        print(f"[SERVER] Initializing GDB for {program_path}...")
        self.gdbmi = GdbController()
        # Load the executable and set arguments immediately
        self.gdbmi.write(f'-file-exec-and-symbols {program_path}')
        self.gdbmi.write('-exec-set-args --nodaemon')
        print("[SERVER] GDB session is configured and ready.")

    def _parse_registers(self, gdb_output):
        regs = {}
        if not gdb_output: return regs
        for record in gdb_output:
            if record.get('message') == 'done' and 'register-values' in record.get('payload', {}):
                for reg in record['payload']['register-values']:
                    regs[reg['name']] = reg['value']
                return regs
        return regs

    def handle_command(self, method, params):
        print(f"[SERVER] Handling command: {method}")
        if method == 'run':
            self.gdbmi.write('-exec-run', timeout_sec=5)
            return {'status': 'program_is_running'}
        
        elif method == 'continue_and_wait_for_crash':
            output = self.gdbmi.write('-exec-continue', timeout_sec=20)
            print(f"[GDB-MI RAW OUTPUT]: {output}")
            is_crash = any("SIGSEGV" in item.get('payload', {}).get('signal-name', '') for item in output)
            return {'crashed': is_crash}

        elif method == 'get_registers':
            output = self.gdbmi.write('-data-list-register-values x eip esp')
            print(f"[GDB-MI RAW OUTPUT]: {output}")
            return {'registers': self._parse_registers(output)}

        elif method == 'execute_shell':
            shell_command = params.get('command')
            print(f"[SERVER] Executing shell: {shell_command}")
            # This must be non-blocking so the GDB server isn't frozen
            subprocess.Popen(shell_command, shell=True, text=True)
            return {'status': 'shell_command_sent'}
        
        return {'error': f'unknown method: {method}'}

    def close(self):
        self.gdbmi.exit()

def main_server_loop(program_path, host='0.0.0.0', port=8080):
    server_logic = GDBServer(program_path)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"[SERVER] GDB MCP Server listening on {host}:{port}")
        conn, addr = s.accept()
        with conn:
            print(f"[SERVER] Agent connected from {addr}")
            buffer = b""
            while True:
                data = conn.recv(4096)
                if not data: break
                buffer += data
                while b'\n' in buffer:
                    message_data, buffer = buffer.split(b'\n', 1)
                    if not message_data: continue
                    command = json.loads(message_data.decode())
                    response = server_logic.handle_command(command.get('method'), command.get('params'))
                    print(f"[SERVER] Sending response: {response}")
                    conn.sendall(json.dumps(response).encode() + b'\n')
    server_logic.close()

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    main_server_loop(sys.argv[1])