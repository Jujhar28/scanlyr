from __future__ import annotations

import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import Settings


def _fernet(settings: Settings) -> Fernet:
    # HKDF label is stable across product renames; changing it invalidates stored Microsoft tokens.
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"shadowtrace:microsoft-graph:token-encryption:v1",
    )
    key_material = hkdf.derive(
        (settings.secret_key + settings.microsoft_graph_token_pepper).encode("utf-8"),
    )
    fernet_key = base64.urlsafe_b64encode(key_material)
    return Fernet(fernet_key)


def encrypt_secret(settings: Settings, plaintext: str) -> str:
    token = _fernet(settings).encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_secret(settings: Settings, ciphertext: str) -> str:
    data = _fernet(settings).decrypt(ciphertext.encode("utf-8"))
    return data.decode("utf-8")
