from typing import Dict, List, Optional, Tuple
import requests

from .constants import BITRISE_API_KEY, BITRISE_ORG_SLUG


class Client:
    def __init__(
        self, api_key: str = BITRISE_API_KEY, org_slug: str = BITRISE_ORG_SLUG
    ):
        self._api_key = api_key
        self._org_slug = org_slug

    @classmethod
    def _get_api_endpoint(cls, path: str) -> str:
        return f"https://api.bitrise.io/v0.1/{path}"

    @classmethod
    def _get_apps_endpoint(cls, path: str) -> str:
        return cls._get_api_endpoint(f"apps/{path}")

    @classmethod
    def _get_app_endpoint(cls, app_slug: str, path: str) -> str:
        return cls._get_apps_endpoint(f"{app_slug}/{path}")

    def _get_request_headers(self) -> dict:
        headers = {
            "Authorization": self._api_key,
            "Content-Type": "application/json",
        }
        return headers

    def get_apps(self) -> List[Dict]:
        response = requests.request(
            url=self._get_api_endpoint(f"apps"),
            method="GET",
            headers=self._get_request_headers(),
            params={"limit": 50},
        )
        json = response.json()
        all_apps = [app for app in json["data"]]
        while "next" in json["paging"]:
            response = requests.request(
                url=self._get_api_endpoint(f"apps"),
                method="GET",
                headers=self._get_request_headers(),
                params={"limit": 50, "next": json["paging"]["next"]},
            )
            json = response.json()
            all_apps.extend(app for app in json["data"])

        return all_apps

    def build(
        self, app_slug: str, workflow_id: str, git_branch: str, clean: bool = False
    ) -> Optional[Tuple[str, str]]:
        build_params = {"branch": git_branch, "workflow_id": workflow_id}
        if clean:
            build_params["environments"] = [
                {
                    "mapped_to": "_OVERRIDE_UCB_CLEAN_BUILD",
                    "value": "True",
                    "is_expand": False,
                }
            ]
        response = requests.request(
            url=self._get_app_endpoint(app_slug, "builds"),
            method="POST",
            headers=self._get_request_headers(),
            json={
                "hook_info": {"type": "bitrise"},
                "build_params": build_params,
            },
        )
        if response.status_code != 201:
            return (response.reason, response.json())

        return None
