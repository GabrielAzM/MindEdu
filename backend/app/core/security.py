import hashlib
import secrets
import string
from datetime import UTC, datetime

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_user_id() -> str:
    alphabet = string.ascii_uppercase + string.digits
    part_a = "".join(secrets.choice(alphabet) for _ in range(4))
    part_b = "".join(secrets.choice(alphabet) for _ in range(4))
    return f"MDU-{part_a}-{part_b}"


def generate_recovery_token() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def utcnow() -> datetime:
    return datetime.now(UTC)
