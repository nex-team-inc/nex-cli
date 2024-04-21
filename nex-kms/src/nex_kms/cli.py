from importlib import resources
from typing import Optional

import click

from .client import Client
from . import decrypt_string


@click.group
def cli():
    """Handle KMS utilities"""
    pass


@cli.command
@click.argument("plaintext_path", type=click.Path(exists=True))
@click.option("--ciphertext_path", "-o", type=click.Path(), default=None)
def encrypt(plaintext_path, ciphertext_path: Optional[str]):
    if ciphertext_path is None or ciphertext_path == "":
        ciphertext_path = (
            f"{plaintext_path[:-4]}.enc"
            if plaintext_path.endswith(".dec")
            else f"{plaintext_path}.enc"
        )
    with open(plaintext_path, "rb") as src_file:
        plaintext = src_file.read()
        client = Client()
        encrypted = client.encrypt_bytes(plaintext)
        with open(ciphertext_path, "wb") as dest_file:
            dest_file.write(encrypted)


@cli.command
@click.argument("ciphertext_path", type=click.Path(exists=True))
@click.option("--plaintext_path", "-o", type=click.Path(), default=None)
def decrypt(ciphertext_path, plaintext_path: Optional[str]):
    if plaintext_path is None or plaintext_path == "":
        plaintext_path = (
            ciphertext_path[:-4]
            if ciphertext_path.endswith(".enc")
            else f"{ciphertext_path}.dec"
        )
    with open(ciphertext_path, "rb") as src_file:
        ciphertext = src_file.read()
        client = Client()
        decrypted = client.decrypt_bytes(ciphertext)
        with open(plaintext_path, "wb") as dest_file:
            dest_file.write(decrypted)


@cli.command
def sample():
    click.echo_via_pager(
        decrypt_string(resources.files() / "secrets" / "sample_message.txt.enc")
    )
