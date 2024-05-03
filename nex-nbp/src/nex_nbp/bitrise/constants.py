from importlib import resources
from nex_kms import decrypt_string

BITRISE_API_KEY = decrypt_string(resources.files() / "secrets/bitrise_api_key.enc")
BITRISE_ORG_SLUG = decrypt_string(resources.files() / "secrets/bitrise_org_slug.enc")
