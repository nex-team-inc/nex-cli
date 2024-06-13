import os
import os.path
from pathlib import Path
from typing import Optional

from git import Repo


class GitInfo:
    @classmethod
    def _find_gitdir(cls) -> Optional[str]:
        if os.path.exists(".git"):
            return "."
        curr = Path(os.getcwd())
        for p in curr.parents:
            if os.path.exists(os.path.join(p, ".git")):
                return str(p)
        return None

    @classmethod
    def create(cls) -> Optional["GitInfo"]:
        gitdir = cls._find_gitdir()
        if gitdir is None:
            return None
        return cls(gitdir)

    def __init__(self, gitdir: str):
        repo = Repo(gitdir)
        self._remote_url = repo.remote("origin").url
        active_branch = repo.active_branch
        tracking_branch = active_branch.tracking_branch()
        self._remote_name = (
            tracking_branch.remote_head
            if tracking_branch is not None
            else active_branch.name
        )

    @property
    def remote_url(self) -> str:
        return self._remote_url

    @property
    def remote_name(self) -> str:
        return self._remote_name
