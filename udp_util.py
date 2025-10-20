#!/usr/bin/env python3
import socket, json, time
from datetime import datetime

CLIENT_PORT = 7500   #clients listen here
SERVER_PORT = 7501   #local server listener

def make_broadcast_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return s

def _env(msg_type, **payload):
    return {
        "type": msg_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": payload
    }

def _send_json(sock, obj, targets):
    data = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    for host, port in targets:
        try:
            sock.sendto(data, (host, port))
            print(f"[udp] sent {len(data)} bytes to {host}:{port}")
        except Exception as e:
            print(f"[udp] error to {host}:{port} -> {e}")

def announce(sock, broadcast_ip, userid, codename, hardware_id, color):
    targets = [(broadcast_ip, CLIENT_PORT), ("127.0.0.1", SERVER_PORT)]
    _send_json(sock, _env("hardware_announce",
                          userid=userid, codename=codename,
                          hardware_id=hardware_id, color=color), targets)

def activate(sock, broadcast_ip, userid, hardware_id, equipment_id):
    targets = [(broadcast_ip, CLIENT_PORT), ("127.0.0.1", SERVER_PORT)]
    _send_json(sock, _env("activate",
                          code=31, userid=userid,
                          hardware_id=hardware_id, equipment_id=equipment_id), targets)

def shutdown(sock, broadcast_ip, userid, hardware_id, repeats=3, delay=0.2):
    targets = [(broadcast_ip, CLIENT_PORT), ("127.0.0.1", SERVER_PORT)]
    for _ in range(repeats):
        _send_json(sock, _env("shutdown", code=221, userid=userid, hardware_id=hardware_id), targets)
        time.sleep(delay)
