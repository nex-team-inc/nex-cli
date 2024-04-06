import click
import os
import requests
import json
import hashlib
import getpass
from pyaxmlparser import APK
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor
from tqdm import tqdm

API_TOKEN = "882e2a898d9197fea25fda6ffff8c16b2a68956abfd275ead614496855ea4608e0ace2e06c687b25d660f3e0e56c8ccb8d3b6da25c0ab8d441a10a4087fd450258563cc9e2ae23b0c98247564443e19eaf877d5766979e174eb933ea40c752a0fb6f9f421cb531b4891077c569004aa15cf01dbf750198352af590ba85855f62"

@click.group()
@click.option("--production", is_flag=True)
def cli(production):
    """PlayOS CMS"""
    global API_URL
    API_URL = "https://cms.x.poseidon.npg.games/api" if production else "https://cms.dev.poseidon.npg.games/api"

@click.command()
@click.argument("file")
def create_release(file):
    """Create a new release by uploading an APK."""

    click.echo(f'CMS API: {API_URL}')

    apk = APK(file)
    click.echo(f'Package: {apk.package}')
    click.echo(f'Version Code: {apk.version_code}')

    md5 = hashlib.md5(open(file, 'rb').read()).hexdigest()
    click.echo(f'MD5: {md5}')

    notes = f'Uploaded via API by {getpass.getuser()}@{os.uname().nodename}. MD5={md5}'
    click.echo(f"Notes: {notes}")

    data = {
        'packageName': apk.package,
        'versionCode': apk.version_code,
        'rolloutGroupMin': 1,
        'rolloutGroupMax': 100,
    }

    encoder = MultipartEncoder({
        'data': json.dumps(data),
        'files.apk': (os.path.basename(file), open(file, 'rb'), 'application/vnd.android.package-archive'),
        'notes': notes,
    })

    progress_bar = tqdm(total=encoder.len, unit='iB', unit_scale=True)

    def progress_bar_callback(monitor):
        progress_bar.update(monitor.bytes_read - progress_bar.n)

    monitor = MultipartEncoderMonitor(encoder, progress_bar_callback)

    response = requests.post(
        API_URL + "/releases",
        data=monitor,
        headers={
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': monitor.content_type,
        })
    
    progress_bar.close()

    if response.status_code == 200:
        res = response.json()
        release_id = res['data']['id']
        click.echo(f'Release ID: {release_id}')
    else:
        click.echo(f'File upload failed: {response.status_code}')
        click.echo(response.text)

cli.add_command(create_release)