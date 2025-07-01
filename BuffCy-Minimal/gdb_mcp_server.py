# gdb_mcp_server.py
import socket
import json
from pygdbmi.gdbcontroller import GdbController
import sys

def run_gdb_server(program_path, host='0.0.0.0', port=8080):
    gdbmi = GdbController()
    
    # Load the program into GDB
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
                    if method == 'run_and_wait_for_crash':
                        gdbmi.write('-exec-run --nodaemon')
                        # This simplified server assumes the next event is a crash
                        output = gdbmi.get_gdb_response(timeout_sec=10) 
                        response['status'] = 'crashed'
                        response['gdb_events'] = output
                    
                    elif method == 'get_registers':
                        response['registers'] = gdbmi.write('-data-list-register-values x eip esp')

                except Exception as e:
                    response['error'] = str(e)
                
                conn.sendall(json.dumps(response).encode())

if __name__ == "__main__":
    run_gdb_server("./connmand")