import importlib.metadata
from importlib.metadata import entry_points, distributions, metadata
import os
import sys

import click

@click.group()
def main():
    '''Main driver'''
    pass

# TODO(matthew_chan): Convert to lazy loading commands.
@main.group
def components():
    pass

discovered = entry_points(group='nexcli.subcommands')
for plugin in discovered:
    main.add_command(plugin.load())

@components.command
def upgrade():
    installed_plugins = set(
        plugin.dist.name for plugin in discovered
    )
    click.echo(f"Discovered plugin: {' '.join(installed_plugins)}")
    os.execv(sys.executable, [sys.executable, '-m', 'pip', 'install', '--upgrade', *installed_plugins])
