import shutil
import click
import os.path
import subprocess
import secrets
import string
from google.cloud import kms
from pyaxmlparser import APK
from rich.console import Console
from rich.live import Live
from rich.table import Table
from nexcli.drive.service import download
from nexcli.utils.locate import find_android_build_tools
from nexcli.utils.uri import is_google_drive_uri

CERT_VALIDITY = 9125

GCP_PROJECT = "playos-signer"
GCP_KMS_LOCATION = "global"
GCP_KMS_KEYRING = "playos-app-signer"

INTERNAL_SIGNER = "playos-apk-signer-1"
EXTERNAL_SIGNER = "playos-apk-signer-2"
PACKAGE_SIGNERS = {
    # Internal games
    "team.nex.arcadexp": INTERNAL_SIGNER,
    "team.nex.archery": INTERNAL_SIGNER,
    "team.nex.basketballknockout": INTERNAL_SIGNER,
    "team.nex.bowling": INTERNAL_SIGNER,
    "team.nex.brickbuster": INTERNAL_SIGNER,
    "team.nex.bunnyhop": INTERNAL_SIGNER,
    "team.nex.elmosays.staging": INTERNAL_SIGNER,
    "team.nex.fitness": INTERNAL_SIGNER,
    "team.nex.galaxyjumper": INTERNAL_SIGNER,
    "team.nex.game2048": INTERNAL_SIGNER,
    "team.nex.gokeeper": INTERNAL_SIGNER,
    "team.nex.hippos": INTERNAL_SIGNER,
    "team.nex.luminous": INTERNAL_SIGNER,
    "team.nex.miniacs": INTERNAL_SIGNER,
    "team.nex.party": INTERNAL_SIGNER,
    "team.nex.peppapig": INTERNAL_SIGNER,
    "team.nex.plane": INTERNAL_SIGNER,
    "team.nex.posediagnostics": INTERNAL_SIGNER,
    "team.nex.starri": INTERNAL_SIGNER,
    "team.nex.sesameflying.staging": INTERNAL_SIGNER,
    "team.nex.tennis": INTERNAL_SIGNER,
    "team.nex.tumbobots": INTERNAL_SIGNER,
    "team.nex.whackamole": INTERNAL_SIGNER,
    # External games
    "team.nex.alieninvasion": EXTERNAL_SIGNER,
    "team.nex.juglr": EXTERNAL_SIGNER,
    "team.nex.neowitch": EXTERNAL_SIGNER,
    "team.nex.starzzle": EXTERNAL_SIGNER,
}


@click.group("apksigner")
def cli():
    """APK signing commands."""
    pass


def run_apksigner(*args, input=None):
    apksigner = os.path.join(find_android_build_tools(), "apksigner")
    run_args = [apksigner]
    run_args.extend(args)
    if input and isinstance(input, str):
        input = input.encode("utf-8")
    return subprocess.run(run_args, check=True, capture_output=True, input=input)


def run_keytool(*args, capture_output=True):
    executable = "keytool"
    if shutil.which(executable) is None:
        raise click.ClickException(f"{executable} not found in PATH. Please setup JDK.")
    run_args = [executable]
    run_args.extend(args)
    return subprocess.run(run_args, check=True, capture_output=capture_output)


def generate_password():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for i in range(24))


def get_keystore_path(name, check=True):
    keystore_path = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "secrets", name + ".jks")
    )
    if check and not os.path.isfile(keystore_path):
        raise click.ClickException(f"Keystore file not found: {keystore_path}")
    return keystore_path


def get_keystore_password_path(name, check=True):
    keystore_path = get_keystore_path(name, check)
    keystore_password_path = os.path.splitext(keystore_path)[0] + "_password.enc"
    if check and not os.path.isfile(keystore_password_path):
        raise click.ClickException(
            f"Keystore password file not found: {keystore_password_path}"
        )
    return (keystore_path, keystore_password_path)


def get_keystore_password(name):
    _, keystore_password_path = get_keystore_password_path(name)
    client = kms.KeyManagementServiceClient()
    key_name = client.crypto_key_path(
        GCP_PROJECT, GCP_KMS_LOCATION, GCP_KMS_KEYRING, name
    )
    with open(keystore_password_path, "rb") as file:
        ciphertext = file.read()
    return client.decrypt(
        request={"name": key_name, "ciphertext": ciphertext}
    ).plaintext


@click.command
@click.argument("apk", type=click.Path(exists=True))
def verify(apk):
    """Verify the signature of an APK"""
    try:
        result = run_apksigner("verify", "--print-certs", "-v", apk)
        click.echo(result.stdout.decode("utf-8").strip())
    except subprocess.CalledProcessError as e:
        click.echo(f'Cannot verify signature: {e.stderr.decode("utf-8")}', err=True)


@click.command
@click.argument("apk")
@click.option("-o", "--output", help="Output file for the signed APK.")
@click.option("--signer", help="Use a different signer for signing.")
def sign(apk, output=None, signer=None):
    """Sign an APK"""
    if is_google_drive_uri(apk):
        click.echo(f"... downloading APK from {apk}")
        apk = download(apk)

    click.echo("... signing APK")

    signapk(apk, output, signer)


def signapk(apk, output=None, signer=None):
    table = Table(show_header=False, show_lines=True)
    with Live(table) as live:
        # Read APK metadata
        metadata = APK(apk)

        # Ensure a signer is defined for the package
        if signer is None:
            signer = PACKAGE_SIGNERS.get(metadata.package)
            if signer is None:
                raise click.ClickException(
                    "No signing credential defined for " + metadata.package
                )

        table.add_row("Input File", apk)
        table.add_row("Package Name", metadata.package)
        table.add_row("Version Code", metadata.version_code)
        live.refresh()

        # Verify the current signature
        try:
            result = run_apksigner("verify", "--print-certs", "-v", apk)
            table.add_row("Current Signature", result.stdout.decode("utf-8").strip())
            live.refresh()
        except subprocess.CalledProcessError as e:
            click.echo(
                f'Cannot verify current signature: {e.stderr.decode("utf-8")}', err=True
            )

        if output is None:
            output = os.path.splitext(apk)[0] + "-signed" + os.path.splitext(apk)[1]
        table.add_row("Output File", output)
        table.add_row("New Signer", signer)
        live.refresh()

        # Sign the APK
        keystore_path = get_keystore_path(signer)
        keystore_password = get_keystore_password(signer)
        try:
            result = run_apksigner(
                "sign",
                "--v4-signing-enabled",
                "false",
                "--ks",
                keystore_path,
                "--ks-pass",
                "stdin",
                "--in",
                apk,
                "--out",
                output,
                input=keystore_password,
            )
        except subprocess.CalledProcessError as e:
            raise click.ClickException(
                "Failed to sign APK: " + e.stderr.decode("utf-8")
            )

        # Verify the new signature
        try:
            result = run_apksigner("verify", "--print-certs", "-v", output)
            table.add_row("New Signature", result.stdout.decode("utf-8").strip())
            live.refresh()
        except subprocess.CalledProcessError as e:
            click.echo(
                f'Cannot verify new signature: {e.stderr.decode("utf-8")}', err=True
            )
    return output


@click.command
@click.argument("signer")
def print_cert(signer):
    """Print a signing certificate"""

    keystore_path = get_keystore_path(signer)
    keystore_password = get_keystore_password(signer)

    click.echo(f"...listing keystore entries at {keystore_path}")

    try:
        run_keytool(
            "-list",
            "-v",
            "-keystore",
            keystore_path,
            "-storepass",
            keystore_password,
            capture_output=False,
        )
    except subprocess.CalledProcessError as e:
        raise click.ClickException(
            f"Failed to list keystore entries: {e.stderr.decode('utf-8')}"
        )


@click.command
@click.argument("signer")
@click.option("-o", "--output", help="Path to the output file.", required=True)
def export_cert(signer, output):
    """Export a signing certificate to a file"""

    keystore_path = get_keystore_path(signer)
    keystore_password = get_keystore_password(signer)

    click.echo(f"... exporting signing certificate from keystore {keystore_path}")

    try:
        run_keytool(
            "-exportcert",
            "-file",
            output,
            "-alias",
            signer,
            "-keystore",
            keystore_path,
            "-storepass",
            keystore_password,
            capture_output=False,
        )
    except subprocess.CalledProcessError as e:
        raise click.ClickException(
            f"Failed to export signing certificate: {e.stderr.decode('utf-8')}"
        )


@click.command
@click.argument("signer")
@click.option("--dname", help='"distinguished name" to use for creating signing key.')
def create_cert(signer, dname):
    """Create a new signing certificate"""
    click.echo(f"... creating new signing certificate")

    keystore_path, keystore_password_path = get_keystore_password_path(
        signer, check=False
    )
    if os.path.isfile(keystore_path):
        raise click.ClickException(f"Keystore file already exists: {keystore_path}")

    console = Console()
    table = Table(show_header=False, show_lines=True)
    table.add_row("Signer", signer)
    table.add_row("Keystore Path", keystore_path)
    table.add_row("Keystore Password Path", keystore_password_path)

    client = kms.KeyManagementServiceClient()
    key_name = client.crypto_key_path(
        GCP_PROJECT, GCP_KMS_LOCATION, GCP_KMS_KEYRING, signer
    )
    table.add_row("GCP KMS Key", key_name)
    console.print(table)

    key_ring_path = client.key_ring_path(GCP_PROJECT, GCP_KMS_LOCATION, GCP_KMS_KEYRING)
    crypto_keys = client.list_crypto_keys({"parent": key_ring_path})
    crypto_key = next((key for key in crypto_keys if key.name == key_name), None)
    if crypto_key is None:
        click.echo(f"... creating new GCP KMS key")
        crypto_key = client.create_crypto_key(
            {
                "parent": key_ring_path,
                "crypto_key_id": signer,
                "crypto_key": {
                    "purpose": kms.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT
                },
            }
        )
    else:
        click.echo(
            f"... using existing GCP KMS key created at {crypto_key.create_time}"
        )

    click.echo(f"... generating and encrypting new keystore password")
    keystore_password = generate_password()
    encrypt_response = client.encrypt(
        {"name": key_name, "plaintext": keystore_password.encode("utf-8")}
    )
    with open(keystore_password_path, "wb") as file:
        file.write(encrypt_response.ciphertext)

    click.echo(f"... creating new signing certificate keystore")
    try:
        genkey_args = [
            "-genkey",
            "-keystore",
            keystore_path,
            "-alias",
            signer,
            "-storepass",
            keystore_password,
            "-validity",
            str(CERT_VALIDITY),
            "-keysize",
            "2048",
            "-keyalg",
            "RSA",
        ]
        if dname:
            genkey_args.extend(["-dname", dname])
        run_keytool(*genkey_args, capture_output=False)
    except subprocess.CalledProcessError as e:
        raise click.ClickException(
            f"Failed to create new signing certificate: {e.stderr.decode('utf-8')}"
        )

    if click.confirm("Print password for backup?"):
        table = Table()
        table.add_column("Keystore Password")
        table.add_row(keystore_password)
        console.print(table)


cli.add_command(sign)
cli.add_command(verify)
cli.add_command(print_cert)
cli.add_command(export_cert)
cli.add_command(create_cert)
