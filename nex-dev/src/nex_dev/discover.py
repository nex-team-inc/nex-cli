import click
import os
import os.path
import sys
from tomllib import load

from .utils import list_versions


@click.command("discover")
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(),
    default="nexcli/src/nexcli/utils/package_list.py",
)
def cli(output_path: str):
    """Generate a .py file with a dictionary on available nexcli subcommand packages and their short description."""
    if not os.path.isdir("nexcli"):
        click.echo(
            "This command should only be run at the parent folder of nexcli.", err=True
        )
        sys.exit(1)

    available = {}
    for name in os.listdir("."):
        if name == "nexcli":
            continue
        if not os.path.isdir(name):
            continue
        pyproject_path = os.path.join(name, "pyproject.toml")
        if not os.path.isfile(pyproject_path):
            continue
        with open(pyproject_path, "rb") as file:
            config = load(file)

        project_config = config.get("project", None)
        if not project_config:
            continue
        entry_points = project_config.get("entry-points", None)
        if not entry_points:
            continue
        subcommands = entry_points.get("nexcli.subcommands", None)
        if not subcommands:
            continue

        # Now check if there is actually an uploaded version.
        package_name = project_config["name"]
        if not list_versions(package_name):
            click.echo(f"Skipping {package_name} because no version was uploaded yet.")
            continue

        available[package_name] = project_config["description"]

    with click.open_file(output_path, "w") as file:
        file.write("### GENERATED ###\n")
        file.write("# fmt: off\n")
        file.write("AVAILABLE = {\n")
        for key, value in sorted(available.items()):
            file.write(f"    {repr(key)}: {repr(value)},\n")
        file.write("}\n")
        file.write("\n# fmt: on\n")
