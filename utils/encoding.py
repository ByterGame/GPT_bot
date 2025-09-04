import base64

def encode_ref(user_id: int) -> str:
    return base64.urlsafe_b64encode(str(user_id).encode()).decode()

def decode_ref(code: str) -> int:
    return int(base64.urlsafe_b64decode(code).decode())
