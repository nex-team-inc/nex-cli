from googleapiclient.http import MediaIoBaseDownload
from .service import create_service, extract_file_id
import click
import io

@click.group('drive')
def cli():
    """Google Drive commands."""
    pass


@click.command()
@click.argument('url', type=str)
def download(url):
    """Download a file from Google Drive from a shareable link."""
    file_id = extract_file_id(url)
    if not file_id:
        click.echo("Invalid Google Drive URL.", err=True)
        return

    try:
        service = create_service()

        # Extract the file name from the file metadata
        file_metadata = service.files().get(fileId=file_id, supportsAllDrives=True).execute()
        file_name = file_metadata.get('name', 'downloaded_file')

        # Download the file
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")

        with open(file_name, 'wb') as f:
            fh.seek(0)
            f.write(fh.read())

        click.echo(f"File '{file_name}' downloaded successfully!")

    except Exception as error:
        raise click.ClickException(str(error))

cli.add_command(download)