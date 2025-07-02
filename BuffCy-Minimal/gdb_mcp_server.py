# gdb_mcp_server.py
import socket
import json
from pygdbmi.gdbcontroller import GdbController
import sys
import subprocess

def parse_registers(gdb_output):
    regs = {}
    if not gdb_output: return regs
    payload = gdb_output[0].get('payload', {})
    reg_values = payload.get('register-values', [])
    for reg in reg_values:
        regs[reg['name']] = reg['value']
    return regs

def run_gdb_server(program_path, host='0.0.0.0', port=8080):
    print(f"[SERVER] Initializing GDB for {program_path}...")
    gdbmi = GdbController()
    gdbmi.write(f'-file-exec-and-symbols {program_path}')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"[SERVER] GDB MCP Server listening on {host}:{port}")
        
        conn, addr = s.accept()
        with conn:
            print(f"[SERVER] Agent connected from {addr}")
            buffer = b""
            while True:
                data = conn.recv(1024)
                if not data: break
                
                buffer += data
                # Process messages delimited by newline
                while b'\n' in buffer:
                    message_data, buffer = buffer.split(b'\n', 1)
                    
                    command = json.loads(message_data.decode())
                    method = command.get('method')
                    params = command.get('params')
                    print(f"[SERVER] Received command: {method}")
                    response = {}

                    try:
                        if method == 'run':
                            gdbmi.write('-exec-run --nodaemon')
                            response['status'] = 'running'
                        elif method == 'get_crash_info':
                            output = gdbmi.get_gdb_response(timeout_sec=15)
                            if any("SIGSEGV" in item.get('payload', '') for item in output if isinstance(item.get('payload'), str)):
                                reg_output = gdbmi.write('-data-list-register-values x eip esp')
                                response['status'] = 'crashed'
                                response['registers'] = parse_registers(reg_output)
                            else:
                                response['status'] = 'no_crash'
                                response['raw_output'] = output
                        elif method == 'execute_shell':
                            shell_command = params.get('command')
                            if shell_command.strip().endswith('&'):
                                subprocess.Popen(shell_command, shell=True, text=True)
                                response['status'] = 'command_started_in_background'
                            else:
                                proc = subprocess.run(shell_command, shell=True, capture_output=True, text=True, timeout=10)
                                response = {'stdout': proc.stdout, 'stderr': proc.stderr, 'exit_code': proc.returncode}

                    except Exception as e:
                        response['error'] = str(e)
                    
                    print(f"[SERVER] Sending response: {response}")
                    conn.sendall(json.dumps(response).encode() + b'\n')

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    run_gdb_server(sys.argv[1])