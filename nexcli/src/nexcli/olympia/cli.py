import click

from nexcli.olympia import apksigner, cms, diag, mixpanel


@click.group("olympia")
def cli():
    """Olympia commands."""
    pass


cli.add_command(mixpanel.cli)
cli.add_command(cms.cli)
cli.add_command(apksigner.cli)
cli.add_command(diag.cli)
