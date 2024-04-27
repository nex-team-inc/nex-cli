import boto3
import click
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearch_dsl import Search, Q
from requests_aws4auth import AWS4Auth

AWS_PROFILE = "nexcli-olympia-opensearch"
OS_AWS_REGION = "us-east-2"
OS_HOST = "os.dev.poseidon.npg.games"
OS_PORT = 443
OS_LOG_INDEX = "android-logs-eng-*"
OS_USERNAME = "nex-support"


@click.command()
@click.argument("device_id")
@click.option("-p", "--password", help="Password to login OpenSearch.")
@click.option("--from", "from_date", default="now-1d", help="Start time of the log.")
@click.option("--to", "to_date", default="now", help="End time of the log.")
@click.option("-l", "--min-level", help="Minimum log level.")
@click.option("-t", "--tag", help="Log tag (support wildcard).")
@click.option("-m", "--message", help="Log message (support wildcard).")
def getlog(device_id, password, from_date, to_date, min_level, tag, message):
    """Get device log from OpenSearch."""

    if password is None:
        session = boto3.Session(profile_name=AWS_PROFILE)
        credentials = session.get_credentials()

        if credentials is None:
            raise click.ClickException(
                'No AWS credentials found. Please sign-in with "aws configure sso"'
            )

        auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            OS_AWS_REGION,
            "es",  # Service code for OpenSearch
            session_token=credentials.token,  # Required if using temporary credentials
        )
    else:
        auth = (OS_USERNAME, password)

    # Creating OS client.
    client = OpenSearch(
        hosts=[{"host": OS_HOST, "port": OS_PORT}],
        http_auth=auth,
        use_ssl=True,
        connection_class=RequestsHttpConnection,
    )

    query = Q("match", deviceId=device_id)
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
