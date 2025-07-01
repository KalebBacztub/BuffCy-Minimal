# main.py
import subprocess
import time
import json
import argparse
from dotenv import load_dotenv
from agent import ExploitAgent

load_dotenv()

def run_exploit(target_binary_name: str, aslr_mode: str):
    """
    The main exploit orchestration logic.
    """
    print(f"***** LAUNCHING EXPLOIT RUN FOR: {target_binary_name} (ASLR: {aslr_mode.upper()}) *****")
    
    # Determine the numeric value for ASLR setting
    aslr_value = "2" if aslr_mode == 'on' else "0"

    # Set the environment variables for docker-compose
    with open('.env', 'w') as f:
        # Note: 'w' mode overwrites the file each run to ensure clean state
        f.write(f"OPENROUTER_API_KEY={os.getenv('OPENROUTER_API_KEY')}\n")
        f.write(f"TARGET_BINARY={target_binary_name}\n")
        f.write(f"ASLR_SETTING={aslr_value}\n")

    # --- Build and Start Containers ---
    print("\nBuilding and starting containers...")
    # Use '--force-recreate' to ensure the target starts fresh with the new ASLR setting
    subprocess.run(["docker", "compose", "up", "--build", "-d", "--force-recreate"])
    
    # Wait for containers to be ready
    print("Waiting for containers to initialize...")
    time.sleep(5) 
    print("Containers are up.")

    try:
        agent = ExploitAgent(model_name="openai/gpt-4o")
        
        print("\n--- Agent is now ready to interact with the target ---")
        print("--- The system is running. Press Ctrl+C to stop. ---")
        # The rest of your agent's interaction logic would go here.
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nUser interrupted. Shutting down...")
    finally:
        # --- Cleanup ---
        print("Stopping and removing containers...")
        subprocess.run(["docker", "compose", "down"])
        print("Cleanup complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BuffCy-Minimal Exploit Agent Runner")
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="The name of the binary in the ./targets/ directory to attack."
    )
    # New argument to control ASLR
    parser.add_argument(
        "--aslr",
        type=str,
        choices=['on', 'off'],
        default='on',
        help="Set ASLR state inside the target container ('on' or 'off')."
    )
    args = parser.parse_args()
    
    run_exploit(args.target, args.aslr)