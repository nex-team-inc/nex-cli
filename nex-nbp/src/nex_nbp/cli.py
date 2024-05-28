from json import dumps
import os.path
from typing import Dict, List, Optional, Sequence

import click
from tabulate import tabulate

from .bitrise import BitriseClient
from .gcp import AppEntry, GCPClient
from .git import GitInfo


@click.group()
def nbp() -> None:
    """Provide utilities of interacting with NBP projects."""
    pass


def _find_app_entry_by_git(
    apps: List[AppEntry], git_info: GitInfo
) -> Optional[AppEntry]:
    remote_url = git_info.remote_url
    for app in apps:
        if app.repo_url == remote_url:
            return app
    return None


def _find_app_entry_by_app_name(
    apps: List[AppEntry], app_name: str
) -> Optional[AppEntry]:
    app_name = app_name.lower()
    for app in apps:
        if app.app_code.lower() == app_name:
            return app

    # We pick the app name that is most suitable.
    for app in apps:
        # Try to find a match.
        if app.title.lower().find(app_name) != -1:
            return app
    # No match, try removing spaces.
    app_name = app_name.replace(" ", "")
    for app in apps:
        if app.title.lower().replace(" ", "").find(app_name) != -1:
            return app
    # Still no match. Try to find one that has the same sequence.
    for app in apps:
        title = app.title.lower().replace(" ", "")
        pos = -1
        for ch in app_name:
            pos = title.find(ch, pos + 1)
            if pos == -1:
                break
        else:
            return app

    return None


_app_name_option = click.option(
    "-a", "--app-name", "app_name", help="App name", type=click.STRING, default=None
)
_branch_option = click.option(
    "-b", "--branch", "branch", help="Git Branch", type=click.STRING, default=None
)


def _find_app_entry(
    apps: List[AppEntry], git_info: Optional[GitInfo], app_name: Optional[str]
) -> Optional[AppEntry]:
    if app_name is not None:
        app_entry = _find_app_entry_by_app_name(apps, app_name)
        if app_entry is None:
            raise click.UsageError(f"Could not find app on bitrise matching {app_name}")
    else:
        if git_info is None:
            raise click.UsageError(
                "Please run inside a git repository to use auto app discovery."
            )
        app_entry = _find_app_entry_by_git(apps, git_info)
        if app_entry is None:
            raise click.UsageError(
                f"Could not find app on bitrise matching git url {git_info.remote_url}"
            )
    return app_entry


def _find_branch(git_info: Optional[GitInfo], branch: Optional[str]) -> str:
    if branch is not None:
        return branch
    if git_info is None:
        raise click.UsageError(
            "Please run inside a git repository to use auto branch detection"
        )
    return git_info.remote_name


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

_staging_option = click.option(
    "-s",
    "--stag/--no-stag",
    "--staging/--no-staging",
    "staging",
    is_flag=True,
    default=None,
)
_production_option = click.option(
    "-p",
    "--prod/--no-prod",
    "--production/--no-production",
    "production",
    is_flag=True,
    default=None,
)
_targets_option = click.option(
    "-t",
    "--target",
    "targets",
    type=click.Choice(("olympia", "sk", "sky", "retail"), case_sensitive=False),
    multiple=True,
    default=("olympia",),
)


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
    if not suffixes:
        raise click.UsageError("No staging nor production, bailing out.")
    return suffixes


@nbp.command()
@_app_name_option
@_branch_option
@_staging_option
@_production_option
@_targets_option
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
    gcp_client = GCPClient()
    all_apps = gcp_client.get_apps()

    app_entry = _find_app_entry(all_apps, git_info, app_name)
    git_branch = _find_branch(git_info, branch)
    suffixes = _compute_suffixes(staging, production)

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
            result = bitrise_client.build(
                app_entry.slug, workflow_id, git_branch, clean
            )
            if result is None:
                click.echo("SUCCESS")
            else:
                click.echo("FAILED")
                click.echo(f"REASON: {result[0]}", err=True)
                click.echo(f"RESPONSE: {result[1]}", err=True)


@nbp.command("list")
def list_projects() -> None:
    """List configured NBP projects."""
    gcp_client = GCPClient()
    all_apps = gcp_client.get_apps()
    table = sorted([app.title, app.repo_url] for app in all_apps)
    headers = ["TITLE", "REPO-URL"]
    click.echo(tabulate(table, headers, tablefmt="simple"))


@nbp.group("builds")
@_app_name_option
@click.option(
    "-b",
    "--branch",
    "branch",
    type=click.STRING,
    help="Specify git branch to filter with.",
    default=None,
)
@click.option(
    "-g",
    "--git-branch",
    "use_git_branch",
    is_flag=True,
    help="Use branch from current git repo.",
    default=False,
)
@_staging_option
@_production_option
@_targets_option
@click.pass_context
def builds(
    ctx: click.Context,
    app_name: Optional[str],
    branch: Optional[str],
    use_git_branch: bool,
    staging: Optional[bool],
    production: Optional[bool],
    targets: Sequence[str],
) -> None:
    """Handle build."""
    ctx.ensure_object(dict)
    git_info = GitInfo.create()
    bitrise_client = BitriseClient()
    ctx.obj["git_info"] = git_info
    ctx.obj["bitrise_client"] = bitrise_client
    gcp_client = GCPClient()
    ctx.obj["gcp_client"] = gcp_client
    all_apps = gcp_client.get_apps()
    ctx.obj["app_entry"] = _find_app_entry(all_apps, git_info, app_name)

    if branch:
        ctx.obj["git_branch"] = branch
    elif use_git_branch:
        if git_info is None:
            raise click.UsageError("Auto git branch is only valid inside a git repo.")
        ctx.obj["git_branch"] = git_info.remote_name
    else:
        ctx.obj["git_branch"] = None

    suffixes = _compute_suffixes(staging, production)
    workflows = []
    for target in targets:
        for suffix in suffixes:
            key = f"{target}#-#{suffix}"
            if key not in _WORKFLOW_MAP:
                click.echo(
                    f"Cannot identify workflow id for {target} {suffix}", err=True
                )
                continue
            workflows.append(_WORKFLOW_MAP[key])
    ctx.obj["workflows"] = workflows


@builds.command("list")
@click.option(
    "-l",
    "--limit",
    type=click.IntRange(min=0, min_open=True),
    help="Limits of entries per workflow.",
    default=3,
)
@click.pass_context
def builds_list(ctx: click.Context, limit: int) -> None:
    """Lists recent completed builds for the given app / branch."""
    app_entry: AppEntry = ctx.obj["app_entry"]
    git_branch: Optional[str] = ctx.obj["git_branch"]
    gcp_client: GCPClient = ctx.obj["gcp_client"]
    workflows: Sequence[str] = ctx.obj["workflows"]
    for workflow in workflows:
        click.echo(f"Workflow {workflow}:")
        for build_entry in gcp_client.find_builds(
            app_entry, git_branch, workflow, limit
        ):
            click.echo(build_entry)


@builds.command()
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=False, exists=True),
    help="Output directory for apks.",
    default=os.path.expanduser("~/Downloads/"),
)
@click.pass_context
def apk(ctx: click.Context, output: str):
    """Download apk for the give app / branch."""
    app_entry: AppEntry = ctx.obj["app_entry"]
    git_branch: Optional[str] = ctx.obj["git_branch"]
    bitrise_client: BitriseClient = ctx.obj["bitrise_client"]
    workflows: Sequence[str] = ctx.obj["workflows"]
    build_dict = bitrise_client.get_post_builds(app_entry.slug, git_branch, workflows)
    for key, (build, apk_artifact) in build_dict.items():
        bitrise_client.download_apk(app_entry.slug, build, apk_artifact, output)
