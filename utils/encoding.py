import base64


def encode_ref(user_id: int) -> str:
    return base64.urlsafe_b64encode(str(user_id).encode()).decode().rstrip("=")

def decode_ref(code: str) -> int | None:
    try:
        padding = 4 - len(code) % 4
        if padding != 4:
            code += "=" * padding
        return int(base64.urlsafe_b64decode(code).decode())
    except Exception:
        return None