import click

from nexcli.drive import service


@click.group('drive')
def cli():
    """Google Drive commands."""
    pass


@click.command()
@click.argument('url', type=str)
def download(url):
    """Download a file from Google Drive from a shareable link."""
    output_file = service.download(url)
    click.echo(f"File '{output_file}' downloaded successfully!")


cli.add_command(download)