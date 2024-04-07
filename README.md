# Nex CLI

## Overview

`nex` is a Python-based CLI tool for Nex employees, streamlining workflows with [Click-powered](https://click.palletsprojects.com/) commands.

## Installation

Install `nex` via pip with:

```bash
pip install git+https://github.com/nex-team-inc/nexcli.git#egg=nexcli
```

## Updating

The `nex` CLI does not update automatically when new changes are pushed to the Git repository.

To update `nex`, run:

```bash
pip install --upgrade git+https://github.com/nex-team-inc/nexcli.git#egg=nexcli
```

## Getting Started

<details>
    <summary>Not available yet</summary>

    Configure your profile with:

    ```bash
    nex config --setup
    ```

</details>

## Usage

For help, type:

```bash
nex --help
```

## Contributing

Clone and set up the repo for contributions:

```bash
git clone https://github.com/nex-team-inc/nexcli.git
git checkout -b feature/your-feature-name
pip install -e .
```

Test changes, follow [Conventional Commits](https://www.conventionalcommits.org/) for messages, and submit pull requests.

```bash
git commit -m "feat: add beta sequence"
```

The commit message contains a type, a scope, and a subject:

- `type`: This describes the kind of change that this commit is providing. Common types include `feat` (a new feature), `fix` (a bug fix), `docs` (changes to documentation), etc.
- `scope` (optional): A scope provides additional contextual information and is contained within parenthesis.
- `subject`: The subject contains a succinct description of the change.

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
