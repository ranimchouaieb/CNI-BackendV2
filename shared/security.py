import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from fastapi import HTTPException, status
from config import settings


def hash_password(password: str) -> str:
    """Hash un mot de passe avec PBKDF2-HMAC-SHA256 (compatible BackendV1)."""
    salt = os.urandom(16)
    iterations = 310_000
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2:sha256:{iterations}${salt.hex()}${key.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie un mot de passe PBKDF2 (compatible BackendV1)."""
    try:
        parts = hashed.split("$")
        if len(parts) != 3 or not parts[0].startswith("pbkdf2:"):
            return False
        algo_part, salt_hex, stored_hex = parts
        _, algo, iterations_str = algo_part.split(":")
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac(algo, plain.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(key.hex(), stored_hex)
    except Exception:
        return False


def create_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({**data, "exp": expire}, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
        )
