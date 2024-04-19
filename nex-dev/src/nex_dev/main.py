from importlib.metadata import EntryPoints, entry_points
from typing import List
import click


class LazySubcommands(click.Group):
    def __init__(
        self,
        *args,
        subcommand_list: EntryPoints = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.subcommand_list = subcommand_list

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


subcommands = entry_points(group="nex-dev.subcommands")


@click.group(cls=LazySubcommands, subcommand_list=subcommands)
def main():
    """Provide various dev tools"""
    pass
