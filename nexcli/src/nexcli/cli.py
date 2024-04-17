from importlib.metadata import EntryPoints, entry_points, distributions, metadata
from typing import List
import os
import sys

import click


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
    "Handle installed components"
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
    installed_plugins = set(plugin.dist.name for plugin in subcommands)
    click.echo(f"Discovered plugin: {' '.join(installed_plugins)}")
    os.execv(
        sys.executable,
        [sys.executable, "-m", "pip", "install", "--upgrade", *installed_plugins],
    )


@components.command
def debug():
    for plugin in subcommands:
        click.echo(f"{plugin.name} from package {plugin.dist.name}")
