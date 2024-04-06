import click
import subprocess
import importlib.resources as pkg_resources

@click.group("adb")
def cli():
    """ADB commands."""
    pass

@cli.command()
def scan():
    """Scan local network for adb devices."""
    # brew install arp-scan expect
    path = pkg_resources.resource_filename('nexcli', 'scripts/adb-scan')
    subprocess.run(path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)