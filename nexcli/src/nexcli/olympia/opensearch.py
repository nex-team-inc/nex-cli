import os
import click
from opensearchpy import OpenSearch

@click.group('opensearch')
def cli():
    """OpenSearch commands."""
    pass

@click.command()
def search():
    """[WIP] Search for logs in OpenSearch."""
    host = 'os.dev.poseidon.npg.games'
    port = 443
    index_name = 'android-logs-eng-*'
    auth = ('nex-support', os.environ.get('PASSWORD'))

    # Creating OS client.
    client = OpenSearch(
        hosts=[{'host': host, 'port': port}],
        http_auth=auth,
        use_ssl=True,
    )

    # This is a query example. This example returns 20 last messages which has field "fields.SubscriptionId" with value "26738458705".
    query = {
        'size': 20,
        'query': {
            "match": {
                "query": "Permission violation"
                # "fields.SubscriptionId": {
                #     "query": "26738458705"
                # }
            }
        }
    }

    # Executing query.
    response = client.search(
        body=query,
        index=index_name
    )

    print('\nSearch results:')
    # Iterating through result and printing message field value to console
    for hit in response['hits']['hits']:
        print('message: ', hit['_source']['message'])

cli.add_command(search)