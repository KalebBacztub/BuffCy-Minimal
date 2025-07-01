# configure_run.py
import argparse

def configure_run(target_binary: str, aslr_mode: str):
    """
    Creates or overwrites the run.env file with the configuration
    for the next docker-compose run.
    """
    aslr_value = "2" if aslr_mode == 'on' else "0"
    
    # Write the run-specific configuration to a separate file
    with open('run.env', 'w') as f:
        f.write(f"TARGET_BINARY={target_binary}\n")
        f.write(f"ASLR_SETTING={aslr_value}\n")
    
    print(f"✅ Configuration set in 'run.env': Target='{target_binary}', ASLR='{aslr_mode.upper()}'")
    print("\nReady to run. Use: docker compose up --build")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure a BuffCy-Minimal run.")
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="The name of the binary in the ./targets/ directory."
    )
    parser.add_argument(
        "--aslr",
        type=str,
        choices=['on', 'off'],
        default='on',
        help="Set ASLR state ('on' or 'off')."
    )
    args = parser.parse_args()
    configure_run(args.target, args.aslr)