import click
import os.path
import sys
import subprocess
import shutil
import secrets
import string
from google.cloud import kms
from pyaxmlparser import APK

DEFAULT_ANDROID_HOME="~/Library/Android/sdk"
CERT_VALIDITY=9125

SIGNING_CREDENTIALS = {
    "team.nex.peppapig": "playos-apk-signer-1",
    "x": "playos-apk-signer-2",
}

@click.group('signapk')
@click.pass_context
# epilog="gcloud CLI, Android Studio and JDK must be installed to use this command. Please read https://www.notion.so/nexteam/App-Signing-CLI-1f1adbc57b1348fbb8dd3b0c352ba38a for setup instructions."
@click.option("--project", help="The Google Cloud project ID to use for KMS operations. If omitted, then the current project of glcoud CLI is assumed.", default="playos-signer")
@click.option("--name", help="Name of the key. Unless otherwise specified, the name of the keystore file, and KMS key are derived from this value.")
@click.option("--kms-key", help="KMS key ID to use for encryption and decryption.")
@click.option("--kms-keyring", help="KMS key ring of the key.", default="playos-app-signer")
@click.option("--kms-location", help="KMS location of the key ring.", default="global")
@click.option("--keystore-path", help="Path of the keystore file. Paths are relative to the \"secrets\" directory.")
@click.option("--keystore-password", help="Password for the keystore. If omitted, uses KMS to encrypt and decrypt the keystore password.")
@click.option("--key-alias", help="Name of the signing key. If omitted, the name without extension of the keystore file will be used.")
@click.option("--dname", help="\"distinguished name\" to use for creating signing key.")
@click.option("--android-home", help="Path to the Android SDK installation directory (ANDROID_HOME)")
@click.option("--gcloud-path", help="Path to the gcloud CLI")
@click.option("--yes", "-y", help="Automatic yes to prompts; assume \"yes\" as answer to all prompts and run non-interactively.", is_flag=True)
def cli(ctx, project, name, kms_key, kms_keyring, kms_location, keystore_path, keystore_password, key_alias, dname, android_home, gcloud_path, yes):
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
    # GCLOUD_PATH = find_gcloud(gcloud_path)
    find_android_sdk_build_tools(android_home)

    ctx.ensure_object(dict)
    ctx.obj['DNAME'] = dname
    ctx.obj['YES'] = yes

def ask_yesno(ctx, prompt, default=False):
    if ctx.obj["YES"]:
        return True
    default_prompt = ' [Y/n]' if default else ' [y/N] '
    answer = input(prompt + default_prompt)
    if answer.lower() in ["y", "yes"]:
        return True
    elif answer.lower() in ["n", "no"]:
        return False
    return default

def find_android_sdk_build_tools(android_home):
    global ANDROID_SDK, ANDROID_BUILD_TOOLS
    ANDROID_SDK = DEFAULT_ANDROID_HOME
    if android_home:
        ANDROID_SDK = android_home
    elif 'ANDROID_HOME' in os.environ:
        ANDROID_SDK = os.environ['ANDROID_HOME']
    ANDROID_SDK = os.path.expanduser(ANDROID_SDK)
    if not os.path.isdir(ANDROID_SDK):
        sys.exit(f"error: Android SDK path is not a directory: {ANDROID_SDK}")
    tmp_build_tools_dir = os.path.join(ANDROID_SDK, 'build-tools')
    if not os.path.isdir(tmp_build_tools_dir):
        sys.exit(f"error: Android SDK does not contain build-tools: {ANDROID_SDK}")
    dirs = os.listdir(tmp_build_tools_dir)
    if len(dirs) == 0:
        sys.exit("error: Android SDK build tools could not be found")
    dirs.sort(reverse=True)
    ANDROID_BUILD_TOOLS = os.path.join(tmp_build_tools_dir, dirs[0])

def find_gcloud(custom_path):
    global GCLOUD_PATH
    if custom_path:
        if os.path.isfile(custom_path):
            GCLOUD_PATH = custom_path
        else:
            sys.exit(f"error: gcloud CLI could not be found at {custom_path}")

    GCLOUD_PATH = shutil.which('gcloud')
    if not GCLOUD_PATH:
        # Homebrew
        if os.path.isfile('/opt/homebrew/share/google-cloud-sdk/bin/gcloud'):
            GCLOUD_PATH = '/opt/homebrew/share/google-cloud-sdk/bin/gcloud'
        else:
            sys.exit("error: gcloud CLI could not be found")

def find_keytool():
    try:
        subprocess.run(['keytool'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        sys.exit("error: keytool or JDK could not be found")

def run_apksigner(args, input=None):
    apksigner_path = os.path.join(ANDROID_BUILD_TOOLS, 'apksigner')
    run_args = [apksigner_path]
    run_args.extend(args)
    if input and isinstance(input, str):
        input = input.encode('utf-8')
    return subprocess.run(run_args, check=True, capture_output=True, input=input)

def run_gcloud(args_, input=None):
    run_args = [GCLOUD_PATH]
    run_args.extend(args_)
    if PROJECT:
        run_args.extend(['--project', PROJECT])
    if input and isinstance(input, str):
        input = input.encode('utf-8')
    return subprocess.run(run_args, check=True, input=input, capture_output=True)

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
@click.pass_context
def verify(ctx, apk):
    """Verify and show information about the APK's signing certificate"""
    try:
        result = run_apksigner(['verify', '-v', '--print-certs', apk])
        print(result.stdout.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))

@click.command
@click.argument("apk")
def sign(apk):
    """Sign the provided APK"""

    metadata = APK(apk)

    click.echo("Package: " + metadata.package)
    click.echo("Version Code: " + metadata.version_code)
    # click.echo("Signature: " + metadata.get_signature())
    # for cert in metadata.get_certificates():
        # click.echo("Certificate: " + cert)

    name = SIGNING_CREDENTIALS.get(metadata.package)
    if name is None:
        raise click.ClickException("No signing credential defined for " + metadata.package)

    apk_signed = os.path.splitext(apk)[0] + '-signed' + os.path.splitext(apk)[1]

    try:
        result = run_apksigner(['verify', '-v', '--print-certs', apk])
        print(f"Current signer of {apk}:")
        print(result.stdout.decode('utf-8'))
    except subprocess.CalledProcessError:
        print("Current APK signature invalid")

    keystore_path = get_keystore_path(name, KEYSTORE_PATH)
    keystore_password = get_keystore_password(name, KMS_KEY, KEYSTORE_PATH, KEYSTORE_PASSWORD)

    try:
        result = run_apksigner(['sign',
                                '--ks', keystore_path,
                                '--ks-pass', 'stdin',
                                '--in', apk,
                                '--out', apk_signed], input=keystore_password)
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))
        sys.exit("error: failed to sign APK")

    try:
        result = run_apksigner(['verify', '-v', '--print-certs', apk_signed])
        print(f"New APK signer of {apk_signed}:")
        print(result.stdout.decode('utf-8'))
    except subprocess.CalledProcessError:
        print("New APK signature invalid")

@click.command
@click.pass_context
def print_cert(ctx):
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
@click.pass_context
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
@click.pass_context
def create_cert(ctx):
    """Create new APK signing certificate"""

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
        if ctx.obj["DNAME"]:
            genkey_args.extend(['-dname', ctx.obj["DNAME"]])
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