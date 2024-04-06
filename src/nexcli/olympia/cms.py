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

@click.command()
@click.option('-l', '--label', required=True, help='A label for the release')
@click.option('-p', '--production', is_flag=True)
@click.argument("apk", type=click.Path(exists=True))
def create_release(apk, label, production):
    """Release an APK by uploading to CMS."""

    api_url = "https://cms.x.poseidon.npg.games/api" if production else "https://cms.dev.poseidon.npg.games/api"
    click.echo(f'CMS API: {api_url}')

    meta = APK(apk)
    with open(apk, 'rb') as file:
        md5 = hashlib.md5(file.read()).hexdigest()
    notes = f'{label}, {apk}, md5={md5}, by {getpass.getuser()}@{os.uname().nodename} via API.'

    data = {
        'packageName': meta.package,
        'versionCode': meta.version_code,
        'rolloutGroupMin': 1,
        'rolloutGroupMax': 100,
        'notes': notes,
    }
    click.echo(json.dumps(data, indent=4))

    with open(apk, 'rb') as file:
        encoder = MultipartEncoder({
            'data': json.dumps(data),
            'files.apk': (os.path.basename(apk), file, 'application/vnd.android.package-archive'),
        })

        progress_bar = tqdm(total=encoder.len, unit='iB', unit_scale=True)

        def progress_bar_callback(monitor):
            progress_bar.update(monitor.bytes_read - progress_bar.n)

        monitor = MultipartEncoderMonitor(encoder, progress_bar_callback)

        response = requests.post(
            api_url + "/releases",
            data=monitor,
            headers={
                'Authorization': f'Bearer {API_TOKEN}',
                'Content-Type': monitor.content_type,
            })

    progress_bar.close()

    if response.status_code == 200:
        res = response.json()
        release_id = res['data']['id']
        click.echo(f'Created release (ID={release_id})')
    else:
        click.echo(f'File upload failed: {response.status_code}')
        click.echo(response.text)
