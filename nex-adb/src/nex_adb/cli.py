import click
from tabulate import tabulate

from .device import Device

@click.group()
def adb() -> None:
    """ADB Utilities."""
    pass


@adb.command()
@click.option("--cache/--no-cache", "use_cache", default=True)
def scan(use_cache: bool) -> None:
    """Scan for nearby Android devices."""
    devices = Device.scan(use_cache)
    click.echo(tabulate([(device.ip, device.serial_num, device.fingerprint) for device in devices], headers=("IP", "Serial Number", "Fingerprint")))
