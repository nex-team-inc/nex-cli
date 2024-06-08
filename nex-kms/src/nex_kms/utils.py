import importlib
import os
import io
from pathlib import Path
import sys

from .constants import (
    DEFAULT_KEY_ID,
    DEFAULT_KEY_RING_ID,
    DEFAULT_LOCATION_ID,
    DEFAULT_PROJECT_ID,
)
from .client import Client

if sys.version_info >= (3, 11):
    from importlib.resources.abc import Traversable
elif sys.version_info >= (3, 9):
    from importlib.abc import Traversable
else:
    from typing import Any

    Traversable = Any


def decrypt(
    cipher_source: bytes | Traversable | str | os.PathLike | io.IOBase,
    key: str = DEFAULT_KEY_ID,
    key_ring: str = DEFAULT_KEY_RING_ID,
    location: str = DEFAULT_LOCATION_ID,
    project: str = DEFAULT_PROJECT_ID,
):
    if isinstance(cipher_source, bytes):
        ciphertext = cipher_source
    elif isinstance(cipher_source, Traversable):
        ciphertext = cipher_source.read_bytes()
    elif isinstance(cipher_source, (str, os.PathLike)):
        with open(cipher_source) as file:
            ciphertext = file.read()
    elif isinstance(cipher_source, io.IOBase):
        ciphertext = cipher_source.read()
    else:
        raise Exception(f"Unsupported cipher_source: {cipher_source}")
    return Client(
        project_id=project, location_id=location, key_ring_id=key_ring, key_id=key
    ).decrypt_bytes(ciphertext)


def decrypt_string(
    cipher_source: bytes | Traversable | str | os.PathLike | io.IOBase,
    key: str = DEFAULT_KEY_ID,
    key_ring: str = DEFAULT_KEY_RING_ID,
    location: str = DEFAULT_LOCATION_ID,
    project: str = DEFAULT_PROJECT_ID,
):
    return decrypt(
        cipher_source, key=key, key_ring=key_ring, location=location, project=project
    ).decode("utf-8")
