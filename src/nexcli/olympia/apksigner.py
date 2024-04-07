import click
import os.path
import sys
import subprocess
import secrets
import string
from google.cloud import kms
from pyaxmlparser import APK
from rich.console import Console
from rich.table import Table
from rich.live import Live
from nexcli.utils.locate import find_android_build_tools

CERT_VALIDITY=9125

SIGNING_CREDENTIALS = {
    "team.nex.peppapig": "playos-apk-signer-1",
    "x": "playos-apk-signer-2",
}

@click.group('apksigner')
@click.option("--project", help="The Google Cloud project ID to use for KMS operations.", default="playos-signer")
@click.option("--name", help="Name of the key. Unless otherwise specified, the name of the keystore file, and KMS key are derived from this value.")
@click.option("--kms-key", help="KMS key ID to use for encryption and decryption.")
@click.option("--kms-keyring", help="KMS key ring of the key.", default="playos-app-signer")
@click.option("--kms-location", help="KMS location of the key ring.", default="global")
@click.option("--keystore-path", help="Path of the keystore file. Paths are relative to the \"secrets\" directory.")
@click.option("--keystore-password", help="Password for the keystore. If omitted, uses KMS to encrypt and decrypt the keystore password.")
@click.option("--key-alias", help="Name of the signing key. If omitted, the name without extension of the keystore file will be used.")
def cli(project, name, kms_key, kms_keyring, kms_location, keystore_path, keystore_password, key_alias):
    """Nex Platform APK signing utility"""
    global PROJECT, NAME, KMS_KEY, KEY_ALIAS, KEYSTORE_PATH, KEYSTORE_PASSWORD, KMS_LOCATION, KMS_KEYRING

    PROJECT = project
    NAME = name
    KMS_KEY = kms_key
    KEY_ALIAS = key_alias
    KEYSTORE_PATH = keystore_path
    KEYSTORE_PASSWORD = keystore_password
    KMS_KEYRING = kms_keyring
    KMS_LOCATION = kms_location

def find_keytool():
    try:
        subprocess.run(['keytool'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        sys.exit("error: keytool or JDK could not be found")

def run_apksigner(*args, input=None):
    apksigner = os.path.join(find_android_build_tools(), 'apksigner')
    run_args = [apksigner]
    run_args.extend(args)
    if input and isinstance(input, str):
        input = input.encode('utf-8')
    return subprocess.run(run_args, check=True, capture_output=True, input=input)

def run_keytool(args, capture_output=True):
    run_args = ['keytool']
    run_args.extend(args)
    return subprocess.run(run_args, check=True, capture_output=capture_output)

def generate_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(24))

def get_keystore_password_path(name, keystore_path):
    keystore_path = get_keystore_path(name, keystore_path)
    (root, _) = os.path.splitext(keystore_path)
    return root + '_password.enc'

def get_keystore_path(name, keystore_path):
    if keystore_path:
        return os.path.realpath(os.path.expanduser(keystore_path))
    if not name:
        sys.exit("error: argument --name or --keystore-path must be specified.")
    return os.path.realpath(os.path.join(os.path.dirname(__file__), 'secrets', name + '.jks'))

def get_kms_key(name, kms_key):
    if kms_key:
        return kms_key
    if not name:
        sys.exit("error: argument --name or --kms-key must be specified.")
    return name

def get_key_alias(name, key_alias):
    if key_alias:
        return key_alias
    if not name:
        sys.exit("error: argument --name or --key-alias must be specified.")
    return name

def gcloud_decrypt_keystore_password(name, kms_key, keystore_path):
    keystore_password_path = get_keystore_password_path(name, keystore_path)
    kms_key = get_kms_key(name, kms_key)
    client = kms.KeyManagementServiceClient()
    key_name = client.crypto_key_path(PROJECT, KMS_LOCATION, KMS_KEYRING, kms_key)
    with open(keystore_password_path, 'rb') as file:
        ciphertext = file.read()
    return client.decrypt(request={
        'name': key_name,
        'ciphertext': ciphertext
    }).plaintext

def get_keystore_password(name, kms_key, keystore_path, keystore_password):
    if keystore_password:
        return keystore_password
    return gcloud_decrypt_keystore_password(name, kms_key, keystore_path)

@click.command
@click.argument("apk", type=click.Path(exists=True))
def verify(apk):
    """Verify the signature of an APK"""
    try:
        result = run_apksigner('verify', '--print-certs', apk)
        click.echo(result.stdout.decode('utf-8').strip())
    except subprocess.CalledProcessError as e:
        click.echo(f'Cannot verify signature: {e.stderr.decode("utf-8")}', err=True)

@click.command
@click.argument("apk", type=click.Path(exists=True))
@click.option("-o", "--output", help="Output file for the signed APK.")
def sign(apk, output=None):
    """Sign an APK"""

    click.echo("Signing APK...")

    metadata = APK(apk)
    name = SIGNING_CREDENTIALS.get(metadata.package)
    if name is None:
        raise click.ClickException("No signing credential defined for " + metadata.package)

    table = Table(show_header=False, show_lines=True)
    table.add_row("Input File", apk)
    table.add_row("Package Name", metadata.package)
    table.add_row("Version Code", metadata.version_code)
    try:
        result = run_apksigner('verify', '--print-certs', apk)
        table.add_row("Current Signature", result.stdout.decode('utf-8').strip())
    except subprocess.CalledProcessError as e:
        click.echo(f'Cannot verify current signature: {e.stderr.decode("utf-8")}', err=True)

    keystore_path = get_keystore_path(name, KEYSTORE_PATH)
    keystore_password = get_keystore_password(name, KMS_KEY, KEYSTORE_PATH, KEYSTORE_PASSWORD)
    if output is None:
        output = os.path.splitext(apk)[0] + '-signed' + os.path.splitext(apk)[1]
    table.add_row("Output File", output)

    with Live(table, console=Console(), refresh_per_second=4):
        try:
            result = run_apksigner('sign',
                                   '--v4-signing-enabled', 'false',
                                   '--ks', keystore_path,
                                   '--ks-pass', 'stdin',
                                   '--in', apk,
                                   '--out', output, input=keystore_password)
        except subprocess.CalledProcessError as e:
            raise click.ClickException("Failed to sign APK: " + e.stderr.decode('utf-8'))

        try:
            result = run_apksigner('verify', '--print-certs', output)
            table.add_row("New Signature", result.stdout.decode('utf-8').strip())
        except subprocess.CalledProcessError as e:
            click.echo(f'Cannot verify new signature: {e.stderr.decode("utf-8")}', err=True)

@click.command
def print_cert():
    """Print information about the signing certificate in the keystore file"""

    find_keytool()

    keystore_path = get_keystore_path(NAME, KEYSTORE_PATH)
    keystore_password = get_keystore_password(NAME, KMS_KEY, KEYSTORE_PATH, KEYSTORE_PASSWORD)

    if not os.path.isfile(keystore_path):
        sys.exit(f"error: keystore file not found: {keystore_path}")

    try:
        print(f"... listing keystore entries ({keystore_path})")
        run_keytool(['-list',
                     '-v',
                     '-keystore', keystore_path,
                     '-storepass', keystore_password], capture_output=False)
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))
        sys.exit('error: failed to create new signing certificate')

@click.command
@click.argument("file")
def export_cert(file):
    """Export the signing certificate in the keystore file"""

    find_keytool()

    keystore_path = get_keystore_path(NAME, KEYSTORE_PATH)
    keystore_password = get_keystore_password(NAME, KMS_KEY, KEYSTORE_PATH, KEYSTORE_PASSWORD)
    key_alias = get_key_alias()

    if not os.path.isfile(keystore_path):
        sys.exit(f"error: keystore file not found: {keystore_path}")

    try:
        print(f"... exporting signing certificate from keystore {keystore_path}")
        run_keytool(['-exportcert',
                     '-file', file,
                     '-alias', key_alias,
                     '-keystore', keystore_path,
                     '-storepass', keystore_password], capture_output=False)
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))
        sys.exit('error: failed to create new signing certificate')

@click.command
@click.option("--dname", help='"distinguished name" to use for creating signing key.')
def create_cert(dname):
    """Create new APK signing certificate"""

    raise click.ClickException("This command is not yet implemented")

    find_keytool()

    if ctx.obj["YES"]:
        sys.exit("error: argument --yes is not allowed when creating keystore")

    keystore_path = get_keystore_path(NAME, KEYSTORE_PATH)
    keystore_password_path = get_keystore_password_path(NAME, KEYSTORE_PATH)
    keystore_password = generate_password()
    kms_key = get_kms_key()
    key_alias = get_key_alias()

    if os.path.isfile(keystore_path):
        sys.exit(f"error: keystore file already exists: {keystore_path}")

    try:
        run_gcloud(['kms', 'keys', 'describe', kms_key,
                    '--location', ctx.obj["KMS_LOCATION"],
                    '--keyring', ctx.obj["KMS_KEYRING"]])
        print(f"... KMS encryption key \"{kms_key}\" is found")
    except subprocess.CalledProcessError:
        try:
            print(f"... creating KMS encryption key \"{kms_key}\"")
            run_gcloud(['kms', 'keys', 'create', kms_key,
                        '--location', ctx.obj["KMS_LOCATION"],
                        '--keyring', ctx.obj["KMS_KEYRING"],
                        '--purpose', 'encryption'])
        except subprocess.CalledProcessError as e:
            print(e.stderr.decode('utf-8'))
            sys.exit('error: failed to create KMS key')

    try:
        print("... saving encrypted keystore password")
        run_gcloud(['kms', 'encrypt',
                    '--plaintext-file', '-',
                    '--ciphertext-file', keystore_password_path,
                    '--location', ctx.obj["KMS_LOCATION"],
                    '--keyring', ctx.obj["KMS_KEYRING"],
                    '--key', kms_key], input=keystore_password)
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))
        sys.exit('error: failed to encrypt keystore password')

    try:
        print("... creating new signing certificate keystore")
        genkey_args = ['-genkey',
                       '-keystore', keystore_path,
                       '-alias', key_alias,
                       '-storepass', keystore_password,
                       '-validity', str(CERT_VALIDITY),
                       '-keysize', '2048',
                       '-keyalg', 'RSA']
        if dname:
            genkey_args.extend(['-dname', dname])
        run_keytool(genkey_args, capture_output=False)
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))
        sys.exit('error: failed to create new signing certificate')

    if ask_yesno('Print password for backup?', default=True):
        print("\nKeystore password:\n")
        print(keystore_password)

cli.add_command(sign)
cli.add_command(verify)
cli.add_command(print_cert)
cli.add_command(export_cert)
cli.add_command(create_cert)