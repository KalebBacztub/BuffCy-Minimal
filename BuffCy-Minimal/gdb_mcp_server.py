# gdb_mcp_server.py
import socket
import json
from pygdbmi.gdbcontroller import GdbController
import sys
import re

def parse_registers(gdb_output):
    """Parses pygdbmi output to a simple dict."""
    regs = {}
    if not gdb_output:
        return regs
    # The payload is in the 'payload' key of the first dictionary
    payload = gdb_output[0].get('payload', {})
    reg_values = payload.get('register-values', [])
    for reg in reg_values:
        regs[reg['name']] = reg['value']
    return regs

def run_gdb_server(program_path, host='0.0.0.0', port=8080):
    gdbmi = GdbController()
    gdbmi.write(f'-file-exec-and-symbols {program_path}')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"GDB MCP Server listening on {host}:{port}")
        
        conn, addr = s.accept()
        with conn:
            print(f"Agent connected from {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                
                command = json.loads(data.decode())
                method = command.get('method')
                response = {}

                try:
                    if method == 'run_and_get_crash_registers':
                        gdbmi.write('-exec-run --nodaemon')
                        # Wait for the program to stop (due to crash)
                        gdbmi.get_gdb_response(timeout_sec=10)
                        
                        # Get register values after the crash
                        reg_output = gdbmi.write('-data-list-register-values x eip esp')
                        response['status'] = 'crashed'
                        response['registers'] = parse_registers(reg_output)
                except Exception as e:
                    response['error'] = str(e)
                
                conn.sendall(json.dumps(response).encode())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gdb_mcp_server.py <path_to_target>")
        sys.exit(1)
    run_gdb_server(sys.argv[1])