import click
import os
import os.path
from typing import Dict, List, Optional, Sequence
from tabulate import tabulate

from .bitrise import BitriseClient
from .git import GitInfo


@click.group()
def nbp() -> None:
    """Provide utilities of interacting with NBP projects."""
    pass


def _find_app_slug_by_git(apps: List[Dict], git_info: GitInfo) -> Optional[str]:
    remote_url = git_info.remote_url
    for app in apps:
        if app["repo_url"] == remote_url:
            return app["slug"]
    return None


def _find_app_slug_by_app_name(apps: List[Dict], app_name: str) -> Optional[str]:
    app_name = app_name.lower()
    # We pick the app name that is most suitable.
    for app in apps:
        # Try to find a match.
        if app["title"].lower().find(app_name) != -1:
            return app["slug"]
    # No match, try removing spaces.
    app_name = app_name.replace(" ", "")
    for app in apps:
        if app["title"].lower().replace(" ", "").find(app_name) != -1:
            return app["slug"]
    # Still no match. Try to find one that has the same sequence.
    for app in apps:
        title = app["title"].lower().replace(" ", "")
        pos = -1
        for ch in app_name:
            pos = title.find(ch, pos + 1)
            if pos == -1:
                break
        else:
            return app["slug"]

    return None


def _compute_suffixes(staging: Optional[bool], production: Optional[bool]) -> List[str]:
    # prod\stag  None  True  False
    #   None      s      s
    #   True      p     sp     p
    #   False     s      s
    if staging is None and not production:
        staging = True
    suffixes = []
    if staging:
        suffixes.append("stag")
    if production:
        suffixes.append("prod")
    return suffixes


_WORKFLOW_MAP = {
    "olympia#-#stag": "build_olympia_apk_staging",
    "olympia#-#prod": "build_olympia_apk_production",
    "sk#-#stag": "build_sk_apk_staging",
    "sk#-#prod": "build_sk_apk_production",
    "sky#-#stag": "build_android_apk_sky_beta",
    "sky#-#prod": "build_android_apk_sky_beta_staging",
    "retail#-#stag": "build_olympia_retail_demo_stag",
    "retail#-#prod": "build_olympia_retail_demo_prod",
}


@nbp.command()
@click.option(
    "-a", "--app-name", "app_name", help="App name", type=click.STRING, default=None
)
@click.option(
    "-b", "--branch", "branch", help="Git Branch", type=click.STRING, default=None
)
@click.option(
    "-s",
    "--stag/--no-stag",
    "--staging/--no-staging",
    "staging",
    is_flag=True,
    default=None,
)
@click.option(
    "-p",
    "--prod/--no-prod",
    "--production/--no-production",
    "production",
    is_flag=True,
    default=None,
)
@click.option(
    "-t",
    "--target",
    "targets",
    type=click.Choice(("olympia", "sk", "sky", "retail"), case_sensitive=False),
    multiple=True,
    default=("olympia",),
)
@click.option("-c", "--clean/--no-clean", "clean", is_flag=True, default=False)
def trigger(
    app_name: Optional[str],
    branch: Optional[str],
    staging: Optional[bool],
    production: Optional[bool],
    targets: Sequence[str],
    clean: bool,
) -> None:
    """Trigger a build through bitrise."""
    git_info = GitInfo.create()
    bitrise_client = BitriseClient()
    all_apps = bitrise_client.get_apps()

    if app_name is not None:
        app_slug = _find_app_slug_by_app_name(all_apps, app_name)
        if app_slug is None:
            click.echo(f"Could not find app on bitrise matching {app_name}", err=True)
            return
    else:
        if git_info is None:
            click.echo(
                "Please run inside a git repository to use auto app discovery.",
                err=True,
            )
            return
        app_slug = _find_app_slug_by_git(all_apps, git_info)
        if app_slug is None:
            click.echo(
                f"Could not find app on bitrise matching git url {git_info.remote_url}",
                err=True,
            )
            return

    suffixes = _compute_suffixes(staging, production)
    if not suffixes:
        click.echo("No staging nor production, bailing out.", err=True)
        return

    if branch is not None:
        git_branch = branch
    else:
        if git_info is None:
            click.echo(
                "Please run inside a git repository to use auto branch detection",
                err=True,
            )
            return
        git_branch = git_info.remote_name

    for target in targets:
        for suffix in suffixes:
            key = f"{target}#-#{suffix}"
            if key not in _WORKFLOW_MAP:
                click.echo(
                    f"Cannot identify workflow id for {target} {suffix}", err=True
                )
                continue
            workflow_id = _WORKFLOW_MAP[key]
            click.echo(f"Triggering {workflow_id} ... ", nl=False)
            result = bitrise_client.build(app_slug, workflow_id, git_branch, clean)
            if result is None:
                click.echo("SUCCESS")
            else:
                click.echo("FAILED")
                click.echo(f"REASON: {result[0]}", err=True)
                click.echo(f"RESPONSE: {result[1]}", err=True)


@nbp.command("list")
def list_projects():
    """List configured NBP projects."""
    bitrise_client = BitriseClient()
    all_apps = bitrise_client.get_apps()
    table = sorted([app["title"], app["repo_url"]] for app in all_apps)
    headers = ["TITLE", "REPO-URL"]
    click.echo(tabulate(table, headers, tablefmt="simple"))
