from typing import Dict, List, Optional

from google.cloud import firestore
import click

from .app_entry import AppEntry
from .constants import GCP_PROJECT, FIRESTORE_DATABASE
from .utils import get_gcp_credentials


class Client:
    _APP_FIELDS = (
        "bitrise_slug",
        "repo_url",
        "title",
    )

    def __init__(self):
        self._client = firestore.Client(
            project=GCP_PROJECT,
            database=FIRESTORE_DATABASE,
            credentials=get_gcp_credentials(),
        )

    def get_apps(self) -> List[AppEntry]:
        ret = []
        projects_ref = self._client.collection("projects")
        for snapshot in projects_ref.stream():
            ret.append(
                AppEntry(
                    snapshot.id,
                    snapshot.get("bitrise_slug"),
                    snapshot.get("repo_url"),
                    snapshot.get("title"),
                )
            )
        return ret

    def list(self, app: AppEntry) -> List[Dict]:
        return []
