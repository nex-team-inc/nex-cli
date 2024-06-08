# NEX Key Management Service Utilities

This is a package for using Google KMS to decode secrets that are shipped with our packages.

Sometimes, it is useful if we can ship some sort of config / secrets that are meant for internal users only. If we ship them as plaintext, getting the source of the package would automatically reveal those files.
It would be better if those information are pre-encrypted, and our package simply decrypt it on the fly if needed. However, we obviously cannot ship the key with the app either, and we need to make sure the current
user is authorized to access those information.

This package leverages the [Google Cloud KMS](https://cloud.google.com/security/products/security-key-management?hl=en) for this job.

## Installation

Simply install this package through `pip` , or declare dependency on this.

```BASH
pip install nex-kms
```

## Usage

For package maintainer, if you are working on the `nexcli` repository, you can use `nex-dev kms` subcommand to invoke KMS commands.

To bundle some secret data in your package, simply put the unencrypted file at your desired location, and run

```BASH
nex-dev kms encrypt "path-to-unencrypted-file"
```

By default, a new file with ".enc" suffix will appear in the same folder, which can be bundled out with the rest of the package.
Please remember to remove / ignore the unencrypted version before building your package and uploading it.

To read this encrypted file in code, please use the following code snippet:

```Python
from importlib import resources
from nex_kms import decrypt

unencrypted = decrypt(resources.files() / ... / encrypted_file.enc)
```

The path to the encrypted file should be supplied using the `resources.files()` API.
To get a string instead of a byte array, replace `decrypt` by `decrypt_string` .

If you do not have access to `nex-dev` , and you need to encrypt content, please use the gcloud command line:

```BASH
gcloud kms encrypt --plaintext-file="source_file" --ciphertext-file="source_file.enc" --key=pipconf --keyring=nexcli --location=global --project="development-179808"
```

In the command, replace source_file with the actual file you want to encrypt.
