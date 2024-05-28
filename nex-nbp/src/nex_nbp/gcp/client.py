from typing import Dict, Iterable, List, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from .app_entry import AppEntry
from .build_entry import BuildEntry
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

    def find_latest_builds(
        self,
        app: AppEntry,
        branch: Optional[str] = None,
        workflow: str = None,
        limit: int = 5,
    ) -> List[BuildEntry]:

        collection_ref: firestore.CollectionReference = (
            self._client.collection("projects")
            .document(app.app_code)
            .collection("builds")
        )
        query = collection_ref.order_by(
            "trigger_timestamp", direction=firestore.Query.DESCENDING
        )
        if branch is not None:
            query = query.where(filter=FieldFilter("branch", "==", branch))
        if workflow is not None:
            query = query.where(filter=FieldFilter("workflow", "==", workflow))
        query = query.limit(limit)

        ret = []
        for snapshot in query.stream():
            ret.append(BuildEntry.from_snapshot(snapshot))
        return ret

    def find_build(self, app: AppEntry, build_num: int) -> Optional[BuildEntry]:
        collection_ref: firestore.CollectionReference = (
            self._client.collection("projects")
            .document(app.app_code)
            .collection("builds")
        )
        snapshot = collection_ref.document(str(build_num)).get()
        if not snapshot.exists:
            return None
        return BuildEntry.from_snapshot(snapshot)
