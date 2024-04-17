# Nex CLI

## Overview

`nex` is a Python-based CLI tool for Nex employees, streamlining workflows with [Click-powered](https://click.palletsprojects.com/) commands.

## Usage

For help, type:

```bash
nex --help
```

### Developing with Click

Learn Click for contributions. Example:

```python
import click

@click.command()
@click.option('--name', prompt='Your name', help='The person to greet.')
def greet(name):
    click.echo(f'Hello {name}!')

if __name__ == '__main__':
    greet()
```

For more, see the [Click documentation](https://click.palletsprojects.com/en/8.0.x/).

### Updating `pyproject.toml`

Add or update dependencies in `pyproject.toml` under `[project.dependencies]`.

## Getting Help

For issues or help, use GitHub issues or the `#team-platform` Slack channel.
