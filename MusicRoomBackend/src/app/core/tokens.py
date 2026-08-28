"""Short, human-shareable secret codes."""

import secrets

# Crockford-ish alphabet: no 0/O/1/I/L to keep codes easy to read aloud and type.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

ACCESS_CODE_LENGTH = 6


def generate_access_code(length: int = ACCESS_CODE_LENGTH) -> str:
    """Return a random uppercase code, e.g. ``"K7Q2M9"``."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))
