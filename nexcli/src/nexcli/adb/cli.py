import click
from pathlib import Path
import subprocess

@click.group("adb")
def cli():
    """ADB commands."""
    pass

@cli.command()
def scan():
    """Scan local network for adb devices and display their serial numbers."""
    base_dir = Path(__file__).resolve().parent
    subprocess.run(str(base_dir / 'adb-scan.sh'))