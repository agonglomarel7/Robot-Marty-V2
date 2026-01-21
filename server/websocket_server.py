# websocket_server.py
import struct
import hashlib
import base64


def recevoir(conn, n):
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def lire_trame(conn):
    header = recevoir(conn, 2)
    if not header:
        return None

    b1, b2 = header
    masked = b2 >> 7
    length = b2 & 0x7F

    if length == 126:
        length = struct.unpack(">H", recevoir(conn, 2))[0]
    elif length == 127:
        length = struct.unpack(">Q", recevoir(conn, 8))[0]

    mask = recevoir(conn, 4) if masked else None
    payload = recevoir(conn, length)

    if masked:
        payload = bytes(payload[i] ^ mask[i % 4] for i in range(length))

    return payload


def send_frame(conn, payload):
    header = b"\x82"
    length = len(payload)

    if length < 126:
        conn.sendall(header + bytes([length]) + payload)
    else:
        conn.sendall(header + b"\x7E" + struct.pack(">H", length) + payload)


def handshake(conn, request):

    try:
        headers = request.decode(errors="ignore").split("\r\n")
    except:
        return

    key = None
    for line in headers:
        if line.lower().startswith("sec-websocket-key"):
            key = line.split(":", 1)[1].strip()

    #CAS MARTY : pas de vraie clé WebSocket
    if key is None:
        print("⚠️ Handshake non standard (Marty) accepté")
        conn.sendall(b"HTTP/1.1 101 Switching Protocols\r\n\r\n")
        return

    #CAS WebSocket classique
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    accept = base64.b64encode(
        hashlib.sha1((key + GUID).encode()).digest()
    ).decode()

    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
    )
    conn.sendall(response.encode())

