import click

from nexcli.drive import service


@click.group("drive")
def cli():
    """Google Drive commands."""
    pass


@click.command()
@click.argument("url", type=str)
def download(url):
    """Download a file from Google Drive from a shareable link."""
    service.download(url)


@click.command()
@click.argument("url", type=str)
def download_folder(url):
    """Download all files from a Google Drive folder link."""
    service.download_folder(url)


cli.add_command(download)
cli.add_command(download_folder)
