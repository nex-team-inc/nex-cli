import argparse
import os.path
import sys
import subprocess
import shutil
import secrets
import string

DEFAULT_ANDROID_HOME="~/Library/Android/sdk"
CERT_VALIDITY=9125

parser = argparse.ArgumentParser(
    prog="sign_apk",
    description="Nex Platform APK signing utility",
    epilog="gcloud CLI, Android Studio and JDK must be installed to use this command. Please read https://www.notion.so/nexteam/App-Signing-CLI-1f1adbc57b1348fbb8dd3b0c352ba38a for setup instructions."
)
parser.add_argument("--sign", help="Sign the provided APK", metavar='APK')
parser.add_argument("--verify", help="Verify and show information about the APK\'s signing certificate", metavar='APK')
parser.add_argument("--print-cert", help="Print information about the signing certificate in the keystore file", action='store_true')
parser.add_argument("--export-cert", help="Export the signing certificate in the keystore file", metavar='FILE')
parser.add_argument("--create-cert", help="Create new APK signing certificate", action='store_true')
parser.add_argument("--project", help="The Google Cloud project ID to use for KMS operations. If omitted, then the current project of glcoud CLI is assumed.")
parser.add_argument("--name", help="Name of the key. Unless otherwise specified, the name of the keystore file, and KMS key are derived from this value.")
parser.add_argument("--kms-key", help="KMS key ID to use for encryption and decryption.")
parser.add_argument("--kms-keyring", help="KMS key ring of the key.", default="nex-app-signing-keys")
parser.add_argument("--kms-location", help="KMS location of the key ring.", default="global")
parser.add_argument("--keystore-path", help="Path of the keystore file. Paths are relative to the \"secrets\" directory.")
parser.add_argument("--keystore-password", help="Password for the keystore. If omitted, uses KMS to encrypt and decrypt the keystore password.")
parser.add_argument("--key-alias", help="Name of the signing key. If omitted, the name without extension of the keystore file will be used.")
parser.add_argument("--dname", help="\"distinguished name\" to use for creating signing key.")
parser.add_argument("--android-home", help="Path to the Android SDK installation directory (ANDROID_HOME)")
parser.add_argument("--gcloud-path", help="Path to the gcloud CLI")
parser.add_argument("--yes", "-y", help="Automatic yes to prompts; assume \"yes\" as answer to all prompts and run non-interactively.", action='store_true')

args=None
android_sdk_dir=None
android_build_tools_dir=None
gcloud_path=None

def ask_yesno(prompt, default=False):
    if args.yes:
        return True
    default_prompt = ' [Y/n]' if default else ' [y/N] '
    answer = input(prompt + default_prompt)
    if answer.lower() in ["y", "yes"]:
        return True
    elif answer.lower() in ["n", "no"]:
        return False
    return default

def find_android_sdk_build_tools():
    global android_sdk_dir, android_build_tools_dir
    android_sdk_dir = DEFAULT_ANDROID_HOME
    if args.android_home:
        android_sdk_dir = args.android_home
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

def find_gcloud():
    global gcloud_path
    if args.gcloud_path:
        if os.path.isfile(args.gcloud_path):
            gcloud_path = args.gcloud_path
        else:
            sys.exit(f"error: gcloud CLI could not be found at {args.gcloud_path}")

    gcloud_path = shutil.which('gcloud')
    if not gcloud_path:
        # Homebrew
        if os.path.isfile('/opt/homebrew/share/google-cloud-sdk/bin/gcloud'):
            gcloud_path = '/opt/homebrew/share/google-cloud-sdk/bin/gcloud'
        else:
            sys.exit("error: gcloud CLI could not be found")

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

def run_gcloud(args_, input=None):
    run_args = [gcloud_path]
    run_args.extend(args_)
    if args.project:
        run_args.extend(['--project', args.project])
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

def get_keystore_path():
    if args.keystore_path:
        return os.path.realpath(os.path.expanduser(args.keystore_path))
    if not args.name:
        sys.exit("error: argument --name or --keystore-path must be specified.")
    basedir = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.realpath(os.path.join(basedir, '../../secrets', args.name + '.jks'))

def get_kms_key():
    if args.kms_key:
        return args.kms_key
    if not args.name:
        sys.exit("error: argument --name or --kms-key must be specified.")
    return args.name

def get_key_alias():
    if args.key_alias:
        return args.key_alias
    if not args.name:
        sys.exit("error: argument --name or --key-alias must be specified.")
    return args.name

def gcloud_decrypt_keystore_password():
    keystore_password_path = get_keystore_password_path()
    kms_key = get_kms_key()

    try:
        print("... decryption keystore password")
        result = run_gcloud(['kms', 'decrypt',
                             '--ciphertext-file', keystore_password_path,
                             '--plaintext-file', '-',
                             '--key', kms_key,
                             '--location', args.kms_location,
                             '--keyring', args.kms_keyring])
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))
        sys.exit('error: failed to decrypt keystore password')

def get_keystore_password():
    if args.keystore_password:
        return args.keystore_password
    return gcloud_decrypt_keystore_password()

def verify():
    find_android_sdk_build_tools()
    try:
        result = run_apksigner(['verify', '-v', '--print-certs', args.verify])
        print(result.stdout.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))

def sign():
    find_gcloud()
    find_android_sdk_build_tools()

    try:
        result = run_apksigner(['verify', '-v', '--print-certs', args.sign])
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
                                args.sign], input=keystore_password)
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))
        sys.exit("error: failed to sign APK")

    try:
        result = run_apksigner(['verify', '-v', '--print-certs', args.sign])
        print("New APK signer:\n")
        print(result.stdout.decode('utf-8'))
    except subprocess.CalledProcessError:
        print("New APK signature invalid")

def print_cert():
    find_gcloud()
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

def export_cert():
    find_gcloud()
    find_keytool()

    keystore_path = get_keystore_path()
    key_alias = get_key_alias()

    keystore_password = get_keystore_password()

    if not os.path.isfile(keystore_path):
        sys.exit(f"error: keystore file not found: {keystore_path}")

    try:
        print(f"... exporting signing certificate from keystore {keystore_path}")
        run_keytool(['-exportcert',
                     '-file', args.export_cert,
                     '-alias', key_alias,
                     '-keystore', keystore_path,
                     '-storepass', keystore_password], capture_output=False)
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))
        sys.exit('error: failed to create new signing certificate')

def create_cert():
    find_gcloud()
    find_keytool()

    if args.yes:
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
                    '--location', args.kms_location,
                    '--keyring', args.kms_keyring])
        print(f"... KMS encryption key \"{kms_key}\" is found")
    except subprocess.CalledProcessError:
        try:
            print(f"... creating KMS encryption key \"{kms_key}\"")
            run_gcloud(['kms', 'keys', 'create', kms_key,
                        '--location', args.kms_location,
                        '--keyring', args.kms_keyring,
                        '--purpose', 'encryption'])
        except subprocess.CalledProcessError as e:
            print(e.stderr.decode('utf-8'))
            sys.exit('error: failed to create KMS key')

    try:
        print("... saving encrypted keystore password")
        run_gcloud(['kms', 'encrypt',
                    '--plaintext-file', '-',
                    '--ciphertext-file', keystore_password_path,
                    '--location', args.kms_location,
                    '--keyring', args.kms_keyring,
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
        if args.dname:
            genkey_args.extend(['-dname', args.dname])
        run_keytool(genkey_args, capture_output=False)
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode('utf-8'))
        sys.exit('error: failed to create new signing certificate')

    if ask_yesno('Print password for backup?', default=True):
        print("\nKeystore password:\n")
        print(keystore_password)

if __name__ == "__main__":
    args=parser.parse_args()
    actions_count = sum(1 if getattr(args, arg) else 0 for arg in ['sign', 'verify', 'print_cert', 'export_cert', 'create_cert'])
    if actions_count > 1:
        sys.exit("error: more than one of --sign, --verify, --print-cert, --export-cert, or --create-cert")

    if args.sign:
        sign()
    elif args.verify:
        verify()
    elif args.print_cert:
        print_cert()
    elif args.export_cert:
        export_cert()
    elif args.create_cert:
        create_cert()
    else:
        sys.exit("error: no action specified")

