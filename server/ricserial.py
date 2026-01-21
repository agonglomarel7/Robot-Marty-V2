# ricserial.py
import json

DELIM = 0xE7


class RICSerialParser:
    """
    Parser minimal RICSerial compatible martypy
    """

    @staticmethod
    def parser(payload: bytes):
        if len(payload) < 2 or payload[0] != DELIM or payload[-1] != DELIM:
            return {"type": "unknown", "raw": payload}

        content = payload[1:-1]
        msg_id = content[0]
        flags = content[2]

        # REST
        if flags == 0x00 and b'\x00' in content[3:]:
            try:
                end = content[3:].index(0x00)
                url = content[3:3+end].decode()
                return {"type": "rest", "id": msg_id, "url": url}
            except:
                pass

        # JSON
        if flags == 0x03:
            try:
                data = json.loads(content[3:-2].decode())
                return {"type": "json", "id": msg_id, "data": data}
            except:
                pass

        return {"type": "binary", "id": msg_id, "data": content[3:]}


class RICSerialGenerator:
    """
    Générateur de réponses RICSerial (CRC simplifié)
    """

    @staticmethod
    def _crc(data):
        c = 0
        for b in data:
            c ^= b
        return c & 0xFF

    @staticmethod
    def ok(msg_id):
        body = bytes([msg_id, 0x02, 0x00]) + b"OK\x00"
        return b"\xE7" + body + bytes([RICSerialGenerator._crc(body)]) + b"\xE7"

    @staticmethod
    def json(msg_id, data):
        payload = json.dumps(data).encode()
        body = bytes([msg_id, 0x02, 0x03]) + payload
        return b"\xE7" + body + bytes([RICSerialGenerator._crc(body)]) + b"\xE7"

    @staticmethod
    def error(msg_id, msg="Error"):
        payload = msg.encode()
        body = bytes([msg_id, 0x02, 0xFF]) + payload + b"\x00"
        return b"\xE7" + body + bytes([RICSerialGenerator._crc(body)]) + b"\xE7"
