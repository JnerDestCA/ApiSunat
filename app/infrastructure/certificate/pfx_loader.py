from __future__ import annotations
from pathlib import Path
from typing import Tuple

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.serialization import pkcs12


def load_pfx(pfx_path: str, password: str) -> Tuple[object, object]:
    path = Path(pfx_path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo PFX no encontrado: {pfx_path}")
    try:
        with open(path, "rb") as f:
            pfx_data = f.read()
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            pfx_data, password.encode("utf-8")
        )
        if private_key is None or certificate is None:
            raise ValueError(
                "El archivo PFX no contiene una clave privada y/o certificado válido"
            )
        return private_key, certificate
    except ValueError as e:
        if "password" in str(e).lower() or "decryption" in str(e).lower():
            raise ValueError("Contraseña del PFX incorrecta") from e
        raise
