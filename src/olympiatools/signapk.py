import click
import os.path
import sys
import subprocess
import shutil
import secrets
import string

DEFAULT_ANDROID_HOME="~/Library/Android/sdk"
CERT_VALIDITY=9125

@click.group()
@click.pass_context
# epilog="gcloud CLI, Android Studio and JDK must be installed to use this command. Please read https://www.notion.so/nexteam/App-Signing-CLI-1f1adbc57b1348fbb8dd3b0c352ba38a for setup instructions."
@click.option("--project", help="The Google Cloud project ID to use for KMS operations. If omitted, then the current project of glcoud CLI is assumed.")
@click.option("--name", help="Name of the key. Unless otherwise specified, the name of the keystore file, and KMS key are derived from this value.")
@click.option("--kms-key", help="KMS key ID to use for encryption and decryption.")
@click.option("--kms-keyring", help="KMS key ring of the key.", default="nex-app-signing-keys")
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
    global PROJECT, GCLOUD_PATH

    PROJECT = project
    GCLOUD_PATH = find_gcloud(gcloud_path)

    ctx.ensure_object(dict)
    ctx.obj['NAME'] = name
    ctx.obj['KMS_KEY'] = kms_key
    ctx.obj['KMS_KEYRING'] = kms_keyring
    ctx.obj['KMS_LOCATION'] = kms_location
    ctx.obj['KEYSTORE_PATH'] = keystore_path
    ctx.obj['KEYSTORE_PASSWORD'] = keystore_password
    ctx.obj['KEY_ALIAS'] = key_alias
    ctx.obj['DNAME'] = dname
    ctx.obj['ANDROID_HOME'] = android_home
    ctx.obj['YES'] = yes

android_sdk_dir=None
android_build_tools_dir=None

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

def find_android_sdk_build_tools(ctx):
    global android_sdk_dir, android_build_tools_dir
    android_sdk_dir = DEFAULT_ANDROID_HOME
    if ctx.obj["ANDROID_HOME"]:
        android_sdk_dir = ctx.obj["ANDROID_HOME"]
    elif 'ANDROID_HOME' in os.environ:
        android_sdk_dir = os.environ['ANDROID_HOME']
    android_sdk_dir = os.path.expanduser(android_sdk_dir)
    if not os.path.isdir(android_sdk_dir):
        sys.exit(f"error: Android SDK path is not a directory: {android_sdk_dir}")
    tmp_build_tools_dir = os.path.join(android_sdk_dir, 'build-tools')
    if not os.path.isdir(tmp_build_tools_dir):
        sys.exit(f"error: Android SDK does not contain build-tools: {android_sdk_dir}")
    dirs = os.listdir(tmp_build_tools_dir)
    if len(dirs) == 0:
        sys.exit("error: Android SDK build tools could not be found")
    dirs.sort(reverse=True)
    android_build_tools_dir = os.path.join(tmp_build_tools_dir, dirs[0])

def find_gcloud(custom_path):
    if custom_path:
        if os.path.isfile(custom_path):
            return custom_path
        else:
            sys.exit(f"error: gcloud CLI could not be found at {custom_path}")

    gcloud_path = shutil.which('gcloud')
    if not gcloud_path:
        # Homebrew
        if os.path.isfile('/opt/homebrew/share/google-cloud-sdk/bin/gcloud'):
            return '/opt/homebrew/share/google-cloud-sdk/bin/gcloud'
        else:
            sys.exit("error: gcloud CLI could not be found")
    else:
        return gcloud_path

def find_keytool():
    try:
        subprocess.run(['keytool'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        sys.exit("error: keytool or JDK could not be found")

def run_apksigner(args, input=None):
    apksigner_path = os.path.join(android_build_tools_dir, 'apksigner')
    run_args = [apksigner_path]
    run_args.extend(args)
    if input and isinstance(input, str):
        input = input.encode('utf-8')
    return subprocess.run(run_args, check=True, capture_output=True, input=input)

def run_gcloud(ctx, args_, input=None):
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

def get_keystore_password_path():
    keystore_path = get_keystore_path()
    (root, _) = os.path.splitext(keystore_path)
    return root + '_password.enc'

def get_keystore_path(ctx):
    if ctx.obj["KEYSTORE_PATH"]:
        return os.path.realpath(os.path.expanduser(ctx.obj["KEYSTORE_PATH"]))
    if not ctx.obj["NAME"]:
        sys.exit("error: argument --name or --keystore-path must be specified.")
    basedir = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.realpath(os.path.join(basedir, '../../secrets', ctx.obj["NAME"] + '.jks'))

def get_kms_key(ctx):
    if ctx.obj["KMS_KEY"]:
        return ctx.obj["KMS_KEY"]
    if not ctx.obj["NAME"]:
        sys.exit("error: argument --name or --kms-key must be specified.")
    return ctx.obj["NAME"]

def get_key_alias(ctx):
    if ctx.obj["KEY_ALIAS"]:
        return ctx.obj["KEY_ALIAS"]
    if not ctx.obj["NAME"]:
        sys.exit("error: argument --name or --key-alias must be specified.")
    return ctx.obj["NAME"]

def gcloud_decrypt_keystore_password(ctx):
    keystore_password_path = get_keystore_password_path()
    kms_key = get_kms_key()

    try:
        print("... decryption keystore password")
        result = run_gcloud(['kms', 'decrypt',
                             '--ciphertext-file', keystore_password_path,
                             '--plaintext-file', '-',
                             '--key', kms_key,
                             '--location', ctx.obj["KMS_LOCATION"],
                             '--keyring', ctx.obj["KMS_KEYRING"]])
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))
        sys.exit('error: failed to decrypt keystore password')

def get_keystore_password(ctx):
    if ctx.obj["KEYSTORE_PASSWORD"]:
        return ctx.obj["KEYSTORE_PASSWORD"]
    return gcloud_decrypt_keystore_password()

@click.command
@click.pass_context
def verify(ctx, apk):
    """Verify and show information about the APK's signing certificate"""

    find_android_sdk_build_tools()
    try:
        result = run_apksigner(['verify', '-v', '--print-certs', apk])
        print(result.stdout.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))

@click.command
@click.argument("apk")
@click.pass_context
def sign(ctx, apk):
    """Sign the provided APK"""

    find_android_sdk_build_tools()

    apk_signed = os.path.splitext(apk)[0] + '-signed' + os.path.splitext(apk)[1]

    try:
        result = run_apksigner(['verify', '-v', '--print-certs', apk])
        print("Current APK signer:\n")
        print(result.stdout.decode('utf-8'))
    except subprocess.CalledProcessError:
        print("Current APK signature invalid")

    confirm = ask_yesno('Do you want to continue?')
    if not confirm:
        sys.exit("error: APK signing cancelled")

    keystore_path = get_keystore_path()
    keystore_password = get_keystore_password()

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
        print("New APK signer:\n")
        print(result.stdout.decode('utf-8'))
    except subprocess.CalledProcessError:
        print("New APK signature invalid")

@click.command
@click.pass_context
def print_cert(ctx):
    """Print information about the signing certificate in the keystore file"""

    find_keytool()

    keystore_path = get_keystore_path()

    keystore_password = get_keystore_password()

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

    keystore_path = get_keystore_path()
    key_alias = get_key_alias()

    keystore_password = get_keystore_password()

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

    keystore_path = get_keystore_path()
    keystore_password_path = get_keystore_password_path()
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