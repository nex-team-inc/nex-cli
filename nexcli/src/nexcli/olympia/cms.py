import click
import os
import requests
import json
import hashlib
import getpass
from pyaxmlparser import APK
from requests_toolbelt.multipart.encoder import (
    MultipartEncoder,
    MultipartEncoderMonitor,
)
from tqdm import tqdm

from nexcli.drive.service import download
from nexcli.olympia.apksigner import signapk
from nexcli.utils.uri import is_google_drive_uri

API_TOKEN = "882e2a898d9197fea25fda6ffff8c16b2a68956abfd275ead614496855ea4608e0ace2e06c687b25d660f3e0e56c8ccb8d3b6da25c0ab8d441a10a4087fd450258563cc9e2ae23b0c98247564443e19eaf877d5766979e174eb933ea40c752a0fb6f9f421cb531b4891077c569004aa15cf01dbf750198352af590ba85855f62"
ALLOWED_APK_PUBLIC_KEYS = [
    "2fa50246e4c67b1c88850e84cb28132422527865d3470072cb21636d876d41dd",
    "74f0220efac6d374d25412656d2a024a76060145c7ebe2a32471b67c32ff9aad",
]


def check_signature(apk):
    """Check signature of the APK similar to util/SignatureVerifier.kt in launcher."""
    click.echo("Approved signer public keys:")
    for allowed in ALLOWED_APK_PUBLIC_KEYS:
        click.echo(f"* {allowed}")

    metadata = APK(apk)
    digests = [
        hashlib.sha256(key).hexdigest() for key in metadata.get_public_keys_der_v2()
    ]

    click.echo("Actual signer public keys:")
    valid_count = 0
    for digest in digests:
        if digest in ALLOWED_APK_PUBLIC_KEYS:
            click.echo(f"+ {digest}")
            valid_count += 1
        else:
            click.echo(f"- {digest}")

    if valid_count == 0:
        raise click.ClickException("APK signature verification failed.")


@click.group("cms")
def cli():
    """CMS commands."""


@click.command()
@click.option("-l", "--label", required=True, help="A label for the release")
@click.option("-p", "--production", is_flag=True)
@click.option("--no-sign", is_flag=True, help="Do not sign the APK")
@click.argument("apk")
def release(apk, label, production, no_sign):
    """Release an APK by uploading to CMS."""

    if is_google_drive_uri(apk):
        click.echo(f"... downloading APK from {apk}")
        apk = download(apk)

    if not no_sign:
        click.echo("... signing APK")
        apk = signapk(apk)

    if production:
        click.echo("... checking APK signature")
        check_signature(apk)

    api_url = (
        "https://cms.x.poseidon.npg.games/api"
        if production
        else "https://cms.dev.poseidon.npg.games/api"
    )
    click.echo(f"... uploading to CMS: {api_url}")

    meta = APK(apk)
    with open(apk, "rb") as file:
        md5 = hashlib.md5(file.read()).hexdigest()
    notes = f"{label}, {apk}, md5={md5}, by {getpass.getuser()}@{os.uname().nodename} via API."

    data = {
        "packageName": meta.package,
        "versionCode": meta.version_code,
        "rolloutGroupMin": 1,
        "rolloutGroupMax": 100,
        "notes": notes,
    }
    click.echo(json.dumps(data, indent=4))

    with open(apk, "rb") as file:
        encoder = MultipartEncoder(
            {
                "data": json.dumps(data),
                "files.apk": (
                    os.path.basename(apk),
                    file,
                    "application/vnd.android.package-archive",
                ),
            }
        )

        progress_bar = tqdm(total=encoder.len, unit="iB", unit_scale=True)

        def progress_bar_callback(monitor):
            progress_bar.update(monitor.bytes_read - progress_bar.n)

        monitor = MultipartEncoderMonitor(encoder, progress_bar_callback)

        response = requests.post(
            api_url + "/releases",
            data=monitor,
            headers={
                "Authorization": f"Bearer {API_TOKEN}",
                "Content-Type": monitor.content_type,
            },
        )

    progress_bar.close()

    if response.status_code == 200:
        res = response.json()
        release_id = res["data"]["id"]
        click.echo(f"Created release (ID={release_id})")
    else:
        click.echo(f"File upload failed: {response.status_code}")
        click.echo(response.text)


cli.add_command(release)
