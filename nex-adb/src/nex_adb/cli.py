import click
from typing import Optional
from nexcli.common import Config

from tabulate import tabulate
from .device import Device


@click.group()
def adb() -> None:
    """ADB Utilities."""
    pass


@adb.command()
def scan() -> None:
    """Scan for nearby Android devices."""
    devices = Device.scan()
    click.echo(
        tabulate(
            [(device.ip, device.serial_num, device.fingerprint) for device in devices],
            headers=("IP", "Serial Number", "Fingerprint"),
        )
    )


@adb.command()
@click.option(
    "--device",
    "-d",
    type=click.STRING,
    default=None,
    help="Set the device IP. Specify - to show a scan menu",
)
@click.option(
    "--package", "-p", type=click.STRING, default=None, help="Set the package."
)
def config(device: Optional[str], package: Optional[str]):
    """Configure running parameters."""
    cfg = Config.get("nex-adb")
    if device is not None:
        if device == "-":
            # We need to do a scanning.
            devices = Device.scan()
            click.echo(
                tabulate(
                    [
                        (idx + 1, device.ip, device.serial_num, device.fingerprint)
                        for idx, device in enumerate(devices)
                    ],
                    headers=("#", "IP", "Serial Number", "Fingerprint"),
                )
            )
            while True:
                picked = click.prompt("Pick a # from the table above.", type=int)
                if picked >= 1 and picked <= len(devices):
                    break
                click.echo(f"Invalid choice {picked}. Please try again.", err=True)
            cfg.set_str("core", "device", devices[picked - 1].ip)
        else:
            cfg.set_str("core", "device", device)
    if package is not None:
        cfg.set_str("core", "package", package)


@adb.command()
@click.option("--package", "-p", type=click.STRING, default=None)
def start(package: Optional[str]) -> None:
    cfg = Config.get("nex-adb")
    ip = cfg.str("core", "device")
    if not ip:
        raise click.UsageError(
            "Please configure device ip through nex adb config --device before using this command."
        )
    device = Device.create(ip)
    if device is None:
        raise click.UsageError(f"Cannot connect to device at {device}")
    if package is None:
        package = cfg.str("core", "package")
    else:
        cfg.set_str("core", "package", package)  # Update last package.
    if package is None:
        raise click.UsageError(f"Package not supplied.")
    device.start(package)


@adb.command()
@click.option("--package", "-p", type=click.STRING, default=None)
def kill(package: Optional[str]) -> None:
    cfg = Config.get("nex-adb")
    ip = cfg.str("core", "device")
    if not ip:
        raise click.UsageError(
            "Please configure device ip through nex adb config --device before using this command."
        )
    device = Device.create(ip)
    if device is None:
        raise click.UsageError(f"Cannot connect to device at {device}")
    if package is None:
        package = cfg.str("core", "package")
    else:
        cfg.set_str("core", "package", package)  # Update last package.
    if package is None:
        raise click.UsageError(f"Package not supplied.")
    device.kill(package)
