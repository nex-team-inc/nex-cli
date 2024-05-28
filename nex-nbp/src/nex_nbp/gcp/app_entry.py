from dataclasses import dataclass


@dataclass(frozen=True)
class AppEntry:
    app_code: str
    slug: str
    repo_url: str
    title: str
