#!/usr/bin/env python3
import socket
PORT = 7501
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", PORT))
print(f"listening on 0.0.0.0:{PORT}")
try:
    while True:
        b, addr = s.recvfrom(4096)
        print(f"\nfrom {addr}:")
        try:
            print(b.decode("utf-8"))
        except:
            print(repr(b))
except KeyboardInterrupt:
    pass
finally:
    s.close()
