import secrets
import hashlib
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Initialize Argon2 PasswordHasher
_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=19456,
    parallelism=1,
    hash_len=32,
    salt_len=16
)


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id."""
    return _hasher.hash(password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    """Verifies a plaintext password against an Argon2 hash."""
    if not hashed_password:
        return False
    try:
        return _hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def generate_activation_token() -> tuple[str, str]:
    """
    Generates a secure, cryptographically random activation token.
    Returns:
        (raw_token, token_hash)
    The raw_token is sent in the email. Only token_hash is stored in the database.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    return raw_token, token_hash


def hash_token(raw_token: str) -> str:
    """Computes a SHA-256 hash of an activation token."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()
