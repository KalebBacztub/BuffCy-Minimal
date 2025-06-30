# gdb_mcp_server.py
import subprocess
import sys
import json
import time

def run_gdb_server(program_path):
    """
    Launches GDB, runs the target, and waits for commands on stdin.
    """
    gdb_command = [
        "gdb",
        "-q",          # Quiet mode
        "--interpreter=mi2", # Use the machine interface
        "--args",
        program_path,
        "--nodaemon"
    ]

    process = subprocess.Popen(
        gdb_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Function to read GDB's output until the '(gdb)' prompt
    def read_gdb_output():
        output = []
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output.append(line)
            # (gdb) prompt indicates GDB is ready for a new command
            if "(gdb)" in line:
                break
        return "".join(output)

    # Initial run to get to a running state
    process.stdin.write("-exec-run\n")
    process.stdin.flush()
    read_gdb_output() # Consume the initial output

    # Main loop to process commands from the agent
    for line in sys.stdin:
        command = line.strip()
        response = {}
        
        try:
            if command == "get_crash_info":
                process.stdin.write("-exec-continue\n")
                process.stdin.flush()
                output = read_gdb_output()

                # Find the signal information for the crash
                for l in output.splitlines():
                    if "SIGSEGV" in l:
                        response['status'] = 'crashed'
                        # Get register info after crash
                        process.stdin.write("-data-list-register-values x eip esp\n")
                        process.stdin.flush()
                        reg_output = read_gdb_output()
                        response['registers'] = reg_output
                        break
                else:
                    response['status'] = 'running'

            elif command.startswith("restart_and_get_esp"):
                process.stdin.write("-exec-run\n")
                process.stdin.flush()
                read_gdb_output()
                
                process.stdin.write("-data-list-register-values x esp\n")
                process.stdin.flush()
                reg_output = read_gdb_output()
                response['registers'] = reg_output
            
            elif command == "check_shell":
                # A simple way to check if a shell spawned is to see if we can send a command
                process.stdin.write("id\n")
                process.stdin.flush()
                time.sleep(1) # Give the shell a moment
                # This is tricky; for a minimal example, we'll just check for GDB's response
                # A real implementation would need more robust shell detection
                output = read_gdb_output()
                if "No such file or directory" in output or "not running" in output:
                     response['shell_active'] = True
                     response['output'] = "Shell appears to be active."
                else:
                    response['shell_active'] = False
                    response['output'] = "No shell detected."

        except Exception as e:
            response['error'] = str(e)

        print(json.dumps(response))
        sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gdb_mcp_server.py <path_to_target>")
        sys.exit(1)
    run_gdb_server(sys.argv[1])