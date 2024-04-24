from typing import AbstractSet
from google.cloud import artifactregistry

from .constants import PROJECT_ID, LOCATION, REPOSITORY


def list_versions(package_name: str) -> AbstractSet[str]:
    client = artifactregistry.ArtifactRegistryClient()
    ret = set()
    page_token = None
    parent_path = client.package_path(PROJECT_ID, LOCATION, REPOSITORY, package_name)
    while True:
        request = artifactregistry.ListVersionsRequest(
            parent=parent_path, page_token=page_token
        )
        response = client.list_versions(request)
        ret.update(
            client.parse_version_path(version.name)["version"]
            for version in response.versions
        )
        page_token = response.next_page_token
        if not page_token:
            break

    return ret
