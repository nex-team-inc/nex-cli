from google.cloud import kms
from google.cloud import kms_v1
import crcmod  # type: ignore

from .constants import (
    DEFAULT_KEY_ID,
    DEFAULT_KEY_RING_ID,
    DEFAULT_LOCATION_ID,
    DEFAULT_PROJECT_ID,
)


class Client:

    shared_client: kms_v1.KeyManagementServiceClient = None

    @classmethod
    def _get_shared_client(cls):
        if cls.shared_client is None:
            cls.shared_client = kms.KeyManagementServiceClient()
        return cls.shared_client

    def __init__(
        self,
        project_id: str = DEFAULT_PROJECT_ID,
        location_id: str = DEFAULT_LOCATION_ID,
        key_ring_id: str = DEFAULT_KEY_RING_ID,
        key_id: str = DEFAULT_KEY_ID,
    ):
        self.key_name = self._get_shared_client().crypto_key_path(
            project_id, location_id, key_ring_id, key_id
        )

    @staticmethod
    def crc32c(data: bytes) -> int:
        """
        Calculates the CRC32C checksum of the provided data.

        Args:
            data: the bytes over which the checksum should be calculated.

        Returns:
            An int representing the CRC32C checksum of the provided bytes.
        """

        crc32c_fun = crcmod.predefined.mkPredefinedCrcFun("crc-32c")
        return crc32c_fun(data)

    def encrypt_bytes(self, plaintext_bytes: bytes) -> bytes:
        plaintext_crc32c = self.crc32c(plaintext_bytes)
        encrypt_response = self._get_shared_client().encrypt(
            request={
                "name": self.key_name,
                "plaintext": plaintext_bytes,
                "plaintext_crc32c": plaintext_crc32c,
            }
        )
        # Optional, but recommended: perform integrity verification on encrypt_response.
        # For more details on ensuring E2E in-transit integrity to and from Cloud KMS visit:
        # https://cloud.google.com/kms/docs/data-integrity-guidelines
        if not encrypt_response.verified_plaintext_crc32c:
            raise Exception("The request sent to the server was corrupted in-transit.")
        if not encrypt_response.ciphertext_crc32c == self.crc32c(
            encrypt_response.ciphertext
        ):
            raise Exception(
                "The response received from the server was corrupted in-transit."
            )
        # End integrity verification

        return encrypt_response.ciphertext

    def decrypt_bytes(self, ciphertext: bytes) -> bytes:
        ciphertext_crc32c = self.crc32c(ciphertext)

        decrypt_response = self._get_shared_client().decrypt(
            request={
                "name": self.key_name,
                "ciphertext": ciphertext,
                "ciphertext_crc32c": ciphertext_crc32c,
            }
        )

        # Optional, but recommended: perform integrity verification on decrypt_response.
        # For more details on ensuring E2E in-transit integrity to and from Cloud KMS visit:
        # https://cloud.google.com/kms/docs/data-integrity-guidelines
        if not decrypt_response.plaintext_crc32c == self.crc32c(
            decrypt_response.plaintext
        ):
            raise Exception(
                "The response received from the server was corrupted in-transit."
            )
        # End integrity verification

        return decrypt_response.plaintext
