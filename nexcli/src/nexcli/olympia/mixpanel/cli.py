import click
from nexcli.olympia.mixpanel import deviceid


@click.group("mixpanel")
def cli():
    """Mixpanel commands."""
    pass


cli.add_command(deviceid.serialno)
