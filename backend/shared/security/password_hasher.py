from __future__ import annotations

import hashlib
import hmac
import secrets

_ITERATIONS = 120_000
_ALGORITHM = "sha256"


def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with a cryptographically secure salt.
    Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        _ALGORITHM,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _ITERATIONS,
    )
    return f"pbkdf2_{_ALGORITHM}${_ITERATIONS}${salt}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against a PBKDF2-HMAC-SHA256 hash.
    Constant-time comparison protects against timing attacks.
    """
    if not plain_password or not hashed_password:
        return False

    # Also support plain comparison for legacy admin default fallback if needed
    if not hashed_password.startswith("pbkdf2_"):
        return hmac.compare_digest(plain_password, hashed_password)

    try:
        parts = hashed_password.split("$")
        if len(parts) != 4:
            return False
        _, iterations_str, salt, original_hash = parts
        iterations = int(iterations_str)
        dk = hashlib.pbkdf2_hmac(
            _ALGORITHM,
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(dk.hex(), original_hash)
    except Exception:
        return False
