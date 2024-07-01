import click
import os.path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple
import requests
from tqdm import tqdm

from .utils import get_bitrise_api_key, get_bitrise_org_slug


class Client:
    def __init__(self, api_key: Optional[str] = None, org_slug: Optional[str] = None):
        self._api_key = api_key if api_key is not None else get_bitrise_api_key()
        self._org_slug = org_slug if org_slug is not None else get_bitrise_org_slug()

    @classmethod
    def _get_api_endpoint(cls, path: str) -> str:
        return f"https://api.bitrise.io/v0.1/{path}"

    @classmethod
    def _get_apps_endpoint(cls, path: str) -> str:
        return cls._get_api_endpoint(f"apps/{path}")

    @classmethod
    def _get_app_endpoint(cls, app_slug: str, path: str) -> str:
        return cls._get_apps_endpoint(f"{app_slug}/{path}")

    @classmethod
    def _get_builds_endpoint(cls, app_slug: str, build_slug: str, path: str) -> str:
        return cls._get_apps_endpoint(f"{app_slug}/builds/{build_slug}/{path}")

    @classmethod
    def _get_artifact_endpoint(
        cls, app_slug: str, build_slug: str, artifact_slug: str
    ) -> str:
        return cls._get_apps_endpoint(
            f"{app_slug}/builds/{build_slug}/artifacts/{artifact_slug}"
        )

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
        response.raise_for_status()
        json = response.json()
        all_apps = [app for app in json["data"]]
        while "next" in json["paging"]:
            response = requests.request(
                url=self._get_api_endpoint(f"apps"),
                method="GET",
                headers=self._get_request_headers(),
                params={"limit": 50, "next": json["paging"]["next"]},
            )
            response.raise_for_status()
            json = response.json()
            all_apps.extend(app for app in json["data"])

        return all_apps

    def build(
        self, app_slug: str, workflow_id: str, git_branch: str, clean: bool = False
    ) -> Tuple[int, str, Dict]:
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
        return (response.status_code, response.reason, response.json())

    def _get_post_builds(self, app_slug: str) -> Iterator[Dict]:
        response = requests.request(
            url=self._get_app_endpoint(app_slug, "builds"),
            method="GET",
            headers=self._get_request_headers(),
            params=dict(workflow="ucb_post_build"),
        )
        response.raise_for_status()
        json = response.json()
        for data in json["data"]:
            yield data
        while "next" in json["paging"]:
            response = requests.request(
                url=self._get_app_endpoint(app_slug, "builds"),
                method="GET",
                headers=self._get_request_headers(),
                params=dict(workflow="ucb_post_build", next=json["paging"]["next"]),
            )
            response.raise_for_status()
            json = response.json()
            for data in json["data"]:
                yield data

    def _fetch_artifacts(self, app_slug: str, build_slug: str) -> Tuple[Dict, Dict]:
        response = requests.request(
            url=self._get_builds_endpoint(app_slug, build_slug, "artifacts"),
            method="GET",
            headers=self._get_request_headers(),
        )
        response.raise_for_status()
        # Find the artifacts with the name env_vars.json, and one with with the .apk suffix
        apk_artifact = None
        env_artifact = None
        for artifact in response.json()["data"]:
            if artifact["title"] == "env_vars.json":
                env_artifact = artifact
            elif artifact["artifact_type"] == "android-apk":
                apk_artifact = artifact
        return (env_artifact, apk_artifact)

    def _get_download_url(
        self, app_slug: str, build_slug: str, artifact_slug: str
    ) -> str:
        response = requests.request(
            url=self._get_artifact_endpoint(app_slug, build_slug, artifact_slug),
            method="GET",
            headers=self._get_request_headers(),
        )
        response.raise_for_status()
        return response.json()["data"]["expiring_download_url"]

    def _fetch_env_vars(
        self, app_slug: str, build_slug: str, env_artifact: Dict
    ) -> Dict:
        download_url = self._get_download_url(
            app_slug, build_slug, env_artifact["slug"]
        )
        downloaded = requests.request(url=download_url, method="GET")
        downloaded.raise_for_status()
        return downloaded.json()

    def get_post_builds(
        self, app_slug: str, git_branch: Optional[str], workflows: List[str]
    ) -> Dict[str, Tuple[Dict, Dict]]:
        ret = {}
        if not workflows:
            return ret
        valid_workflows = set(workflows)
        num_remaining = len(valid_workflows)
        for build in self._get_post_builds(app_slug):
            build_slug = build["slug"]
            env_artifact, apk_artifact = self._fetch_artifacts(app_slug, build_slug)
            if env_artifact is None or apk_artifact is None:
                continue
            env_vars = self._fetch_env_vars(app_slug, build_slug, env_artifact)
            workflow_id = env_vars["TRIGGER_STAGE_BITRISE_TRIGGERED_WORKFLOW_ID"]
            if workflow_id not in valid_workflows:
                continue
            if workflow_id in ret:
                continue
            if (
                git_branch is not None
                and env_vars["TRIGGER_STAGE_BITRISE_GIT_BRANCH"] != git_branch
            ):
                continue
            ret[workflow_id] = (build, apk_artifact)
            num_remaining -= 1
            if num_remaining == 0:
                break

        return ret

    def download_artifact(
        self, app_slug: str, build_slug: str, artifact_slug: str, out_dir: str
    ) -> None:
        response = requests.request(
            url=self._get_artifact_endpoint(app_slug, build_slug, artifact_slug),
            method="GET",
            headers=self._get_request_headers(),
        )
        response.raise_for_status()
        metadata = response.json()["data"]

        file_size_bytes = metadata["file_size_bytes"]
        download_url = self._get_download_url(app_slug, build_slug, artifact_slug)
        output_file = os.path.join(out_dir, metadata["title"])
        click.echo(f"Downloading to {output_file}")
        click.echo(f"Download URL: {download_url}")
        with requests.get(download_url, stream=True) as req:
            req.raise_for_status()
            with open(output_file, "wb") as file:
                with tqdm(total=file_size_bytes, unit="b", unit_scale=True) as pbar:
                    for chunk in req.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            pbar.update(len(chunk))

    def download_apk(
        self, app_slug: str, build: Dict, apk_artifact: Dict, out_dir: str
    ) -> None:
        build_slug = build["slug"]
        artifact_slug = apk_artifact["slug"]
        file_size_bytes = apk_artifact["file_size_bytes"]
        download_url = self._get_download_url(app_slug, build_slug, artifact_slug)
        output_file = os.path.join(out_dir, apk_artifact["title"])
        click.echo(f"Downloading to {output_file}")
        click.echo(f"Download URL: {download_url}")
        with requests.get(download_url, stream=True) as req:
            req.raise_for_status()
            with open(output_file, "wb") as file:
                with tqdm(total=file_size_bytes, unit="b", unit_scale=True) as pbar:
                    for chunk in req.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            pbar.update(len(chunk))
