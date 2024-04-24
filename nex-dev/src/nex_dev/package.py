import click
import os.path
from semver import Version
from shutil import rmtree
import subprocess
import sys
from tomlkit import load, dump
from typing import Optional

from .constants import REPO_URL
from .utils import list_versions

SRC_KEY = "src"
DIST_KEY = "dist"


@click.group(name="package", chain=True)
@click.option(
    "--source",
    "-s",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--dist",
    default="dist",
    type=click.STRING,
    help="The relative path to the build/distribution folder",
)
@click.pass_context
def cli(ctx: click.Context, source: str, dist: str):
    """Handle various development tasks"""
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)

    ctx.obj[SRC_KEY] = source
    ctx.obj[DIST_KEY] = dist

    # Check if this is a valid directory with pyproject.toml
    if not os.path.isfile(os.path.join(source, "pyproject.toml")):
        raise Exception("Invalid package directory", "pyproject.toml not found")


@cli.command("build")
@click.option("--clean/--no-clean", default=True)
@click.pass_context
def build(ctx: click.Context, clean: bool):
    """Builds the package at the current directory"""
    dist = ctx.obj[DIST_KEY]
    source = ctx.obj[SRC_KEY]
    if clean and os.path.isdir(dist):
        rmtree(dist, ignore_errors=True)
    subprocess.run([sys.executable, "-m", "build", "--outdir", dist, source])


@cli.command("upload")
@click.pass_context
def upload(ctx: click.Context):
    """Upload the built current package, dist default at dist."""
    dist_dir = os.path.join(ctx.obj[SRC_KEY], ctx.obj[DIST_KEY])

    subprocess.run(
        [
            sys.executable,
            "-m",
            "twine",
            "upload",
            "--repository-url",
            REPO_URL,
            *[os.path.join(dist_dir, name) for name in os.listdir(dist_dir)],
        ]
    )


@cli.command("bump")
@click.option(
    "--part",
    "-p",
    type=click.Choice(("major", "minor", "patch", "prerelease"), case_sensitive=False),
    default="patch",
)
@click.option(
    "--remote/--no-remote",
    "-r",
    default=True,
)
@click.pass_context
def increment_version(
    ctx: click.Context, part: Optional[str] = "patch", remote: bool = True
):
    config_path = os.path.join(ctx.obj[SRC_KEY], "pyproject.toml")
    with open(config_path, "rb") as file:
        doc = load(file)
    project_name = doc["project"]["name"]
    curr_version = Version.parse(doc["project"].get("version", "0.0.0"))
    existing_versions = (
        list_versions(project_name) if remote else set((str(curr_version),))
    )
    # Let's start bumping.
    while str(curr_version) in existing_versions:
        curr_version = curr_version.next_version(part)

    doc["project"]["version"] = str(curr_version)
    with open(config_path, "w") as file:
        dump(doc, file)
