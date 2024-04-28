import datetime
import boto3
import click
import tqdm


def s3_client(env):
    suffix = "prod" if env == "prd" else "test"
    session = boto3.Session(profile_name=f"nexcli-olympia-bugreport-{suffix}")
    return session.client("s3")


def bucket_name(env):
    return f"nex-use2-{env}01-reports"


@click.group("bugreport")
def cli():
    """Bugreport commands."""
    pass


@click.command()
@click.argument("name")
@click.option("--env", default="prd", help="One of dev, stg and prd (default).")
@click.option("-o", "--output", help="Output file name.")
def download(name, env, output=None):
    """Download a specific bugreport."""

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
    """List bugreports for a device."""

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


cli.add_command(download)
cli.add_command(list)
