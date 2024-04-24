from importlib.metadata import EntryPoints, entry_points, Distribution
from typing import List
import os
import sys

import click

from .utils.package_list import AVAILABLE
from .utils.package import is_editable, is_valid_package_for_install


class LazySubcommands(click.Group):
    def __init__(
        self,
        *args,
        subcommand_list: EntryPoints = None,
        components_group: "click.Group" = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.subcommand_list = subcommand_list
        self.components_group = components_group

    def list_commands(self, ctx: click.Context) -> List[str]:
        base = super().list_commands(ctx)
        lazy = [entry_point.name for entry_point in self.subcommand_list]
        return sorted(base + lazy)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        try:
            entry_point = self.subcommand_list[cmd_name]
            return entry_point.load()
        except KeyError:
            pass
        return super().get_command(ctx, cmd_name)


@click.group
def components():
    "Handles components / subcommands."
    pass


subcommands = entry_points(group="nexcli.subcommands")


@click.group(
    cls=LazySubcommands,
    subcommand_list=subcommands,
    components_group=components,
    help="Main Driver",
)
def main():
    pass


main.add_command(components)


@components.command
def upgrade():
    """Upgrade all installed components"""
    installed_plugins = set(
        plugin.dist.name for plugin in subcommands if not is_editable(plugin.dist)
    )
    if len(installed_plugins) == 0:
        click.echo("Cannot find any upgradable plugin.")
        return
    click.echo(f"Discovered upgradable plugin(s): {' '.join(installed_plugins)}")
    os.execv(
        sys.executable,
        [sys.executable, "-m", "pip", "install", "--upgrade", *installed_plugins],
    )


@components.command
def discover():
    for package_name, description in AVAILABLE.items():
        click.echo(f"{package_name}: {description}")

@components.command
@click.argument("packages", type=click.Choice(AVAILABLE.keys(), case_sensitive=True), nargs=-1)
def install(packages):
    """Install packages for nexcli."""
    unique_names = set(packages)
    # Find those that are not editable.
    valid_names = [pkg for pkg in unique_names if is_valid_package_for_install(pkg)]
    if not valid_names:
        click.echo("Please specify non-editable package(s) for installation.")
    else:
        os.execv(
            sys.executable,
            [sys.executable, "-m", "pip", "install", "--upgrade", *valid_names],
        )


@components.command
def list():
    """List installed subcommands and packages."""
    # Build a map from package name to subcommands.
    package_map = {}
    # First column is package-names.
    # Second column is editability.
    # Third column is subcommand lists.
    header0 = "PACKAGE"
    header1 = "EDITABLE"
    header2 = "SUBCOMMAND"
    len0 = len(header0)
    len1 = len(header1)
    len2 = len(header2)
    for plugin in subcommands:
        package_name = plugin.dist.name
        if package_name not in package_map:
            package_map[package_name] = {'is_editable': is_editable(plugin.dist), 'subcommands': []}
        package_map[package_name]['subcommands'].append(plugin.name)
        if len(package_name) > len0:
            len0 = len(package_name)
        if len(plugin.name) > len2:
            len2 = len(plugin.name)

    # Now print the table.
    click.echo(f"{"=" * (len0 + len1 + len2 + 6)}")
    click.echo(f"{header0:{len0}} | {header1:{len1}} | {header2}")
    separator =f"{"-" * len0}-+-{"-" * len1}-+-{"-"*len2}" 
    package_names = sorted(package_map.keys())
    filler0 = " " * len0
    filler1 = " " * len1
    for package_name in package_names:
        click.echo(separator)
        data = package_map[package_name]
        data0 = package_name + " " * (len0 - len(package_name))
        data1 = ("Y" if data['is_editable'] else "N") + " " * (len1 - 1)
        for subcmd in sorted(data['subcommands']):
            click.echo(f"{data0} | {data1} | {subcmd}")
            data0 = filler0
            data1 = filler1
    click.echo(f"{"=" * (len0 + len1 + len2 + 6)}")
