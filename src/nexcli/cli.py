import click

from . import adb, cms, deviceid, signapk
from .drive.cli import download

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
main.add_command(cms.cli, "cms")
drive.add_command(download)
