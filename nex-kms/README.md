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

For package maintainer
