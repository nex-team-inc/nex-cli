import boto3
import click
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearch_dsl import Search, Q
from requests_aws4auth import AWS4Auth

@click.group('opensearch')
def cli():
    """OpenSearch commands."""
    pass

@click.command()
@click.argument('device_id')
@click.option('-p', '--password', help='Password for OpenSearch.')
def search(device_id, password):
    """Search for an eng device logs in OpenSearch."""
    host = 'os.dev.poseidon.npg.games'
    port = 443
    index_name = 'android-logs-eng-*'

    if password is None:
        session = boto3.Session(profile_name="nexcli-olympia-opensearch")
        credentials = session.get_credentials()

        if credentials is None:
            raise click.ClickException('No AWS credentials found. Please sign-in with "aws configure sso"')

        auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            'us-east-2',
            'es',  # Service code for OpenSearch
            session_token=credentials.token  # Required if using temporary credentials
        )
    else:
        auth = ('nex-support', password)

    # Creating OS client.
    client = OpenSearch(
        hosts=[{'host': host, 'port': port}],
        http_auth=auth,
        use_ssl=True,
        connection_class=RequestsHttpConnection,
    )

    query = Q("match", deviceId=device_id) & Q("range", **{"@timestamp": {"gte": "now-1d", "lte": "now"}})
    search = Search(using=client, index=index_name)
    search = search.query(query)
    search = search.sort('@timestamp')

    start = 0
    page_size = 500
    results = []
    while True:
        search = search[start:start + page_size]
        results = search.execute()

        if not results.hits:
            break

        for hit in results.hits:
            timestamp = getattr(hit, "@timestamp")
            click.echo(f"{timestamp} {hit.pid: >5d} {hit.tid: >5d} {hit.level[0].capitalize()} {hit.tag}: {hit.message}")

        start += page_size


cli.add_command(search)