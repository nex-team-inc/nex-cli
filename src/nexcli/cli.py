import click
from . import adb, drive, olympia

@click.group()
def main():
    pass

main.add_command(adb.cli)
main.add_command(drive.cli)
main.add_command(olympia.cli)