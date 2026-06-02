"""Unit tests for the core security primitives.

Covers password hashing/verification, invite token generation and hashing,
and the cookie-signing helpers.  All tested functions are pure (no I/O or
database calls required).
"""

from __future__ import annotations

import pytest

from amc.core.security import (
    generate_invite_token,
    hash_password,
    hash_token,
    make_signer,
    needs_rehash,
    sign_value,
    unsign_value,
    verify_password,
)


class TestPasswordHashing:
    """Argon2id hash and verify helpers."""

    @pytest.mark.unit
    def test_hash_and_verify_correct(self) -> None:
        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed) is True

    @pytest.mark.unit
    def test_wrong_password_returns_false(self) -> None:
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    @pytest.mark.unit
    def test_invalid_hash_returns_false(self) -> None:
        assert verify_password("anything", "not-a-valid-hash") is False

    @pytest.mark.unit
    def test_needs_rehash_fresh_hash_is_false(self) -> None:
        hashed = hash_password("test")
        assert needs_rehash(hashed) is False


class TestInviteToken:
    """Invite-token generation and SHA-256 hashing."""

    @pytest.mark.unit
    def test_generate_token_is_non_empty(self) -> None:
        token = generate_invite_token()
        assert len(token) > 20

    @pytest.mark.unit
    def test_tokens_are_unique(self) -> None:
        assert generate_invite_token() != generate_invite_token()

    @pytest.mark.unit
    def test_hash_token_returns_hex_digest(self) -> None:
        digest = hash_token("my-token")
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    @pytest.mark.unit
    def test_hash_token_is_deterministic(self) -> None:
        assert hash_token("abc") == hash_token("abc")


class TestCookieSigning:
    """Cookie signing and unsigning with SHA-256 HMAC."""

    @pytest.mark.unit
    def test_make_signer_returns_signer(self) -> None:
        signer = make_signer("my-secret")
        assert signer is not None

    @pytest.mark.unit
    def test_sign_and_unsign_roundtrip(self) -> None:
        secret = "super-secret-key"
        value = "session-id-12345"
        signed = sign_value(secret, value)
        assert unsign_value(secret, signed) == value

    @pytest.mark.unit
    def test_unsign_wrong_secret_returns_none(self) -> None:
        signed = sign_value("real-secret", "data")
        assert unsign_value("wrong-secret", signed) is None

    @pytest.mark.unit
    def test_unsign_tampered_returns_none(self) -> None:
        assert unsign_value("secret", "tampered.invalidsig") is None

    @pytest.mark.unit
    def test_signed_value_differs_from_original(self) -> None:
        signed = sign_value("key", "value")
        assert signed != "value"
