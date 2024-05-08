import datetime
import boto3
import click
from opensearch_dsl import Q, Search
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import tqdm

OS_AWS_PROFILE = "nexcli-olympia-opensearch"
OS_AWS_REGION = "us-east-2"
OS_HOST = "os.dev.poseidon.npg.games"
OS_PORT = 443
OS_LOG_INDEX = "android-logs-eng-*"
OS_USERNAME = "nex-support"
OS_PASSWORD = "8z~KzyTqzJAO56iX"

DEVICE_ALIAS = {"david": "902795HP52A000005"}


def s3_client(env):
    suffix = "prod" if env == "prd" else "test"
    session = boto3.Session(profile_name=f"nexcli-olympia-bugreport-{suffix}")
    return session.client("s3")


def bucket_name(env):
    return f"nex-use2-{env}01-reports"


def secretmanager_client(env):
    suffix = "prod" if env == "prd" else "test"
    session = boto3.Session(profile_name=f"nexcli-olympia-bugreport-{suffix}")
    return session.client("secretmanager")


def os_client():
    # Creating OS client.
    return OpenSearch(
        hosts=[{"host": OS_HOST, "port": OS_PORT}],
        http_auth=(OS_USERNAME, OS_PASSWORD),
        use_ssl=True,
        connection_class=RequestsHttpConnection,
    )


@click.group("diag")
def cli():
    """Online diagnostic data commands."""
    pass


@click.command()
@click.argument("name")
@click.option("--env", default="prd", help="One of dev, stg and prd (default).")
@click.option("-o", "--output", help="Output file name.")
def download(name, env, output=None):
    """Download a specific diagnostic report."""

    if not name.endswith(".zip"):
        name += ".zip"

    if output is None:
        output = name

    try:
        client = s3_client(env)
        file_size = client.head_object(Bucket=bucket_name(env), Key=name)[
            "ContentLength"
        ]
        with tqdm.tqdm(total=file_size, unit="B", unit_scale=True, desc=name) as pbar:
            client.download_file(
                bucket_name(env),
                name,
                output,
                Callback=pbar.update,
            )

    except Exception as e:
        raise click.ClickException(e)


@click.command()
@click.option("--env", default="prd", help="One of dev, stg and prd (default).")
@click.option("--max-age", default=7, help="Maximum age in days (default to 7).")
def list(env, max_age):
    """List diagnostic reports."""

    try:
        client = s3_client(env)

        now = datetime.datetime.now(datetime.UTC)
        start_date = (now - datetime.timedelta(days=max_age)).strftime("%y-%m-%d")
        click.echo(f"Listing reports since: {start_date} (UTC)")

        # List all objects in S3 bucket with the prefix "report_"
        response = client.list_objects_v2(
            Bucket=bucket_name(env), StartAfter=f"report_{start_date}_"
        )
    except Exception as e:
        raise click.ClickException(e)

    # Print all object keys in response.
    for obj in response.get("Contents", []):
        click.echo(obj["Key"])

    pass


@click.command()
@click.argument("deviceid")
@click.option("--from", "from_date", default="now-1d", help="Start time of the log.")
@click.option("--to", "to_date", default="now", help="End time of the log.")
@click.option("-l", "--min-level", help="Minimum log level.")
@click.option("-t", "--tag", help="Log tag (support wildcard).")
@click.option("-m", "--message", help="Log message (support wildcard).")
def log(deviceid, from_date, to_date, min_level, tag, message):
    """Get device log from OpenSearch."""

    if deviceid in DEVICE_ALIAS:
        deviceid = DEVICE_ALIAS[deviceid]

    client = os_client()
    query = Q("match", deviceId=deviceid)
    query &= Q("range", **{"@timestamp": {"gte": from_date, "lte": to_date}})
    if min_level is not None:
        matched_levels = []
        for l in ["error", "warn", "info", "debug", "verbose"]:
            matched_levels.append(l)
            if min_level[0].lower() == l[0]:
                break
        query &= Q("terms", level=matched_levels)
    if tag is not None:
        query &= Q("wildcard", tag={"value": tag})
    if message is not None:
        query &= Q("wildcard", message={"value": message})

    search = Search(using=client, index=OS_LOG_INDEX)
    search = search.query(query)
    search = search.sort("@timestamp")

    start = 0
    page_size = 500
    results = []
    while True:
        search = search[start : start + page_size]
        results = search.execute()

        if not results.hits:
            break

        for hit in results.hits:
            timestamp = getattr(hit, "@timestamp")
            click.echo(
                f"{timestamp} {hit.pid: >5d} {hit.tid: >5d} {hit.level[0].capitalize()} {hit.tag}: {hit.message}"
            )

        start += page_size


cli.add_command(download)
cli.add_command(list)
cli.add_command(log)
