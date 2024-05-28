from dataclasses import dataclass
from typing import Optional


@dataclass
class BuildEntry:
    build_num: int
    branch: Optional[str]
    workflow: str
    timestamp: int
    app_build_num: Optional[str]
    apk_slug: Optional[str]
    apk_size: Optional[int]
