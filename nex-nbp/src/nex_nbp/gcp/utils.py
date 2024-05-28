from functools import cache
from importlib import resources
from json import loads
from typing import Dict

from google.oauth2 import service_account

from nex_kms import decrypt_string


@cache
def get_gcp_credentials() -> service_account.Credentials:
    json = loads(decrypt_string(resources.files() / "secrets/gcp_nbp_sa_key.json.enc"))
    return service_account.Credentials.from_service_account_info(json)
