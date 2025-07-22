import hashlib
import os
from typing import Optional

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash password with salt using SHA256 (placeholder; use argon2/bcrypt in prod)."""
    if not salt:
        salt = os.urandom(16).hex()
    pwd = f"{salt}{password}".encode("utf-8")
    return f"{salt}${hashlib.sha256(pwd).hexdigest()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if plain password matches the hashed one."""
    salt, hash_ = hashed_password.split("$")
    return hash_password(plain_password, salt) == hashed_password

def create_access_token(user_id: int) -> str:
    """Dummy JWT token generator (replace with real JWT implementation)."""
    # In prod, use a JWT library. Here we simulate for demo.
    return f"token-{user_id}"

def verify_access_token(token: str) -> Optional[int]:
    """Simple token parser to extract user id from 'token-<id>' format."""
    try:
        if token.startswith("token-"):
            return int(token.split("-")[1])
    except Exception:
        pass
    return None
