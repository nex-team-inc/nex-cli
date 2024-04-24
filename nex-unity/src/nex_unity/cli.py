import click
import os.path
from importlib import resources
from nex_kms import decrypt


@click.group()
def unity():
    pass


# cspell:ignore upmconfig
CONFIG_FILENAME = "upmconfig.toml"


@unity.command()
def setup_upm():
    config_path = os.path.expanduser(f"~/.{CONFIG_FILENAME}")
    click.echo(f'Writing to "{config_path}"')
    with click.open_file(config_path, "wb") as file:
        file.write(decrypt(resources.files() / f"secrets/{CONFIG_FILENAME}.enc"))
