import click

from olympiatools import adb, deviceid
from olympiatools.drive.cli import download

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
drive.add_command(download)
