from functools import cache
from importlib import resources
from nex_kms import decrypt_string


@cache
def get_bitrise_api_key():
    return decrypt_string(resources.files() / "secrets/bitrise_api_key.enc")


@cache
def get_bitrise_org_slug():
    return decrypt_string(resources.files() / "secrets/bitrise_org_slug.enc")
