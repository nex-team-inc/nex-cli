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
from rich.console import Console
from rich.table import Table
from tqdm import tqdm

from nexcli.drive.service import download
from nexcli.olympia.apksigner import signapk
from nexcli.utils.uri import is_google_drive_uri

if False:
    import http.client as http_client

    http_client.HTTPConnection.debuglevel = 1

    import logging

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

CMS_HOST_PROD = "cms.poseidon.npg.games"
CMS_HOST_DEV = "cms.dev.poseidon.npg.games"
ALLOWED_APK_PUBLIC_KEYS = [
    "2fa50246e4c67b1c88850e84cb28132422527865d3470072cb21636d876d41dd",
    "74f0220efac6d374d25412656d2a024a76060145c7ebe2a32471b67c32ff9aad",
]


def cms_hostname(is_prod):
    return CMS_HOST_PROD if is_prod else CMS_HOST_DEV


def cms_api(is_prod):
    return f"https://{cms_hostname(is_prod)}/api"


def token_file_path(is_prod):
    return os.path.expanduser(
        "~/.nexcli/olympia_cms_api_token_" + cms_hostname(is_prod)
    )


def get_token(is_prod):
    with open(token_file_path(is_prod), "r") as file:
        return file.read().strip()


def set_token(is_prod, token):
    os.makedirs(os.path.dirname(token_file_path(is_prod)), exist_ok=True)
    with open(token_file_path(is_prod), "w") as file:
        file.write(token)


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
    pass


@click.command()
@click.argument("token")
@click.option("-p", "--production", "is_prod", is_flag=True)
def auth(token, is_prod):
    """Setup API authorization token."""

    set_token(is_prod, token)


@click.command()
@click.option("-l", "--label", required=True, help="A label for the release")
@click.option("-p", "--production", "is_prod", is_flag=True)
@click.option("--no-sign", is_flag=True, help="Do not sign the APK")
@click.argument("apk")
def publish(apk, label, is_prod, no_sign):
    """Publish (release) an APK by uploading to CMS."""

    if is_google_drive_uri(apk):
        click.echo(f"... downloading APK from {apk}")
        apk = download(apk)

    if not no_sign:
        click.echo("... signing APK")
        apk = signapk(apk)

    if is_prod:
        click.echo("... checking APK signature")
        check_signature(apk)

    api_url = cms_api(is_prod)
    api_token = get_token(is_prod)
    click.echo(f"... uploading to CMS: {api_url}")

    meta = APK(apk)
    with open(apk, "rb") as file:
        md5 = hashlib.md5(file.read()).hexdigest()
    notes = f"{label}, {apk}, md5={md5}, by {getpass.getuser()}@{os.uname().nodename} via API."

    data = {
        "packageName": meta.package,
        "versionCode": meta.version_code,
        "rolloutGroupMin": 0,
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
                "Authorization": f"Bearer {api_token}",
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


# packageName=team.nex.something&environment=default&rolloutGroup=1
@click.command()
@click.argument("pkg_name")
@click.option(
    "-e",
    "--environment",
    default="default",
    help='The release environment (default = "default").',
)
@click.option(
    "-g", "--rollout-group", default=1, help="The rollout group (default = 1)."
)
@click.option("-p", "--production", "is_prod", is_flag=True)
def latest(pkg_name, environment, rollout_group, is_prod):
    """Show the latest release for a package."""

    api_url = cms_api(is_prod)
    api_token = get_token(is_prod)

    params = {
        "packageName": pkg_name,
        "environment": environment,
        "rolloutGroup": rollout_group,
    }

    res = requests.get(
        api_url + "/releases",
        params=params,
        headers={
            "Authorization": f"Bearer {api_token}",
        },
    )

    if res.status_code != 200:
        # print(res.headers)
        message = res.json().get("error", {}).get("message", res.text)
        raise click.ClickException(f"{res.status_code} {message}")

    data = res.json().get("data", {})
    release_attrs = data.get("attributes", {})
    apk_attrs = release_attrs.get("apk", {}).get("data", {}).get("attributes", {})

    table = Table(show_header=False, show_lines=True)
    table.add_row("ID", str(data["id"]))
    table.add_row("Package Name", release_attrs["packageName"])
    table.add_row("Version Code", str(release_attrs["versionCode"]))
    table.add_row("URL", apk_attrs["url"])
    table.add_row("Filename", apk_attrs["name"])
    table.add_row("Size", f"{apk_attrs["size"] / 1024:.0f} MB")
    table.add_row("Updated", apk_attrs["updatedAt"])

    console = Console()
    console.print(table)


if False:
    @click.command()
    @click.argument("pkg_name")
    @click.option(
        "-a", "--all", is_flag=True, help="List all releases, including inactive ones."
    )
    @click.option(
        "-e", "--environment", help="Include only releases in a specific environment."
    )
    @click.option("-p", "--production", "is_prod", is_flag=True)
    def list(pkg_name, all, environment, is_prod):
        """List releases in CMS."""

        api_url = cms_api(is_prod)
        api_token = get_token(is_prod)

        params = {
            "sort[0]": "versionCode:desc",
            "filters[packageName][$eq]": pkg_name,
        }
        if environment:
            params["filters[environments][$eq]"] = environment

        res = requests.get(
            api_url + "/releases",
            params=params,
            headers={
                "Authorization": f"Bearer {api_token}",
            },
        )

        if res.status_code != 200:
            # print(res.headers)
            message = res.json().get("error", {}).get("message", res.text)
            raise click.ClickException(f"{res.status_code} {message}")

        data = res.json()

        if data["meta"]["pageCount"] > 1:
            click.echo(f"... showing first {data.meta.pageSize}")

        table = Table(show_header=True)
        table.add_column("Package Name")
        table.add_column("Version Code")
        table.add_column("Rollout Group")
        table.add_column("Environment(s)")
        table.add_column("Notes")
        for item in data["data"]:
            table.add_row(
                item.attributes.packageName,
                item.attributes.versionCode,
                f"{item.attributes.rolloutGroupMin}-{item.attributes.rolloutGroupMax}",
                ", ".join(item.attributes.environments),
                item.attributes.notes,
            )
        table.print()


cli.add_command(auth)
cli.add_command(latest)
cli.add_command(publish)
