import click

from . import adb, deviceid
from .drive.cli import download
from . import signapk

@click.group()
def main():
    pass

@click.group()
def drive():
    """Google Drive commands."""
    pass

main.add_command(adb.cli)
main.add_command(drive)
main.add_command(deviceid.decode)
main.add_command(signapk.cli, "signapk")
drive.add_command(download)
