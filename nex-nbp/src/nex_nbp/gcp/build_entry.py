from dataclasses import dataclass
from typing import Optional

from google.cloud.firestore import DocumentSnapshot


@dataclass
class BuildEntry:
    build_num: int
    build_slug: str
    branch: Optional[str]
    workflow: str
    timestamp: int
    app_build_num: Optional[str]
    apk_slug: Optional[str]
    apk_size: Optional[int]

    @classmethod
    def from_snapshot(cls, snapshot: DocumentSnapshot) -> "BuildEntry":
        return cls(
            int(snapshot.id),
            snapshot.get("post_build_slug"),
            snapshot.get("branch"),
            snapshot.get("workflow"),
            snapshot.get("trigger_timestamp"),
            snapshot.get("app_build_number"),
            snapshot.get("apk_slug"),
            snapshot.get("apk_size"),
        )

    @property
    def post_build_url(self) -> str:
        return f"https://app.bitrise.io/build/{self.build_slug}"

    @property
    def apk_download_url(self) -> str:
        if self.apk_slug is None:
            return ""
        return f"https://app.bitrise.io/artifact/{self.apk_slug}/download"
