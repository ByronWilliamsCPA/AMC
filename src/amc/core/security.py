"""Password hashing, invite-token, and session-cookie signing primitives.

Centralises the cryptographic choices required by ``docs/planning/tech-spec.md``
(Security) and the FIPS guidance in ``CLAUDE.md``:

- **Passwords**: Argon2id via ``argon2-cffi`` (not bcrypt).
- **Invite tokens**: a high-entropy random token shared once; only its SHA-256
  hash is stored.
- **Session cookies**: the opaque session id is carried in a signed cookie using
  ``itsdangerous`` with an explicit SHA-256 HMAC (the library default is SHA-1,
  which is prohibited under FIPS for security use).
"""

from __future__ import annotations

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions
from itsdangerous import BadSignature, Signer
from itsdangerous import exc as itsdangerous_exc

# A single, reusable Argon2 hasher with library-default (OWASP-aligned)
# parameters. Argon2id is the default variant.
_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return an Argon2id hash of a plaintext password.

    Args:
        password: The plaintext password.

    Returns:
        The encoded Argon2 hash, safe to store in the database.
    """
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored Argon2 hash.

    Args:
        password: The plaintext password to check.
        password_hash: The stored Argon2 hash.

    Returns:
        True when the password matches; False on any mismatch or malformed hash.
    """
    try:
        return _password_hasher.verify(password_hash, password)
    except (
        argon2_exceptions.VerifyMismatchError,
        argon2_exceptions.VerificationError,
        argon2_exceptions.InvalidHashError,
    ):
        return False


def needs_rehash(password_hash: str) -> bool:
    """Return whether a stored hash should be upgraded to current parameters.

    Args:
        password_hash: The stored Argon2 hash.

    Returns:
        True when the hash was produced with weaker parameters than current.
    """
    return _password_hasher.check_needs_rehash(password_hash)


def generate_invite_token() -> str:
    """Return a new high-entropy invite token (the raw secret, shared once).

    Returns:
        A URL-safe random token. Only its :func:`hash_token` digest is stored.
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of an invite token.

    SHA-256 is FIPS-approved; invite tokens carry their own entropy so a salt is
    unnecessary and a deterministic digest is required for lookup.

    Args:
        token: The raw invite token.

    Returns:
        The hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def make_signer(secret: str) -> Signer:
    """Return an itsdangerous signer using an explicit SHA-256 HMAC.

    The library default digest is SHA-1, which is prohibited for security use
    under FIPS; this pins SHA-256.

    Args:
        secret: The signing secret.

    Returns:
        A configured :class:`itsdangerous.Signer`.
    """
    return Signer(secret, digest_method=hashlib.sha256)


def sign_value(secret: str, value: str) -> str:
    """Sign an opaque value (e.g. a session id) for cookie transport.

    Args:
        secret: The signing secret.
        value: The value to sign.

    Returns:
        The signed token (``value.signature``).
    """
    return make_signer(secret).sign(value).decode("utf-8")


def unsign_value(secret: str, signed: str) -> str | None:
    """Recover and verify a signed value, or return ``None`` if tampered.

    Args:
        secret: The signing secret used to sign the value.
        signed: The signed token from the cookie.

    Returns:
        The original value when the signature is valid, else ``None``.
    """
    try:
        return make_signer(secret).unsign(signed).decode("utf-8")
    except (BadSignature, itsdangerous_exc.BadData):
        return None
