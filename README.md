# Nex CLI

## Overview

Welcome to the official repository of the `nex` CLI. `nex` is a comprehensive utility developed in Python, designed to encapsulate a collection of useful commands for employees at Nex. It streamlines various company-specific workflows, making it an essential tool for anyone working at Nex.

The tool is built using the [Click](https://click.palletsprojects.com/) library, which allows for the creation of clean and easy-to-use command line interfaces in Python. Click is a modern framework for building command line applications and provides out-of-the-box support for argument parsing, help text generation, and much more.

## Installation

The `nex` CLI can be installed directly from the Git repository via `pip`. To install `nex`, ensure you have Python and `pip` installed on your system, then run the following command:

```bash
pip install git+https://github.com/nex-team-inc/nexcli.git#egg=nexcli
```

## Updating

The `nex` CLI does not update automatically when new changes are pushed to the Git repository. To update your installed nex tool to the latest version, you need to run the installation command again with the `--upgrade` flag:

```bash
pip install --upgrade git+https://github.com/nex-team-inc/nexcli.git#egg=nexcli
```

This command will uninstall the current version of `nex` and reinstall the latest version from the Git repository.

## Getting Started

<details>
    <summary>Not available yet</summary>

    After installation, you can run the `nex` command to see a list of available subcommands and their descriptions. To get started, you might want to configure your personal settings:

    ```bash
    nex config --setup
    ```

    This will guide you through setting up your `nex` profile.
</details>

## Usage

Here are some basic commands to get you started:

- View help information:

```bash
nex --help
```

## Participating in Development

Development of `nex` is done openly on GitHub. We encourage all employees to contribute to the tool by submitting pull requests, reporting bugs, and suggesting enhancements.

To contribute:

1. Clone the repository:

    ```bash
    git clone https://github.com/nex-team-inc/nexcli.git
    ```

2. Create a new branch for your feature or fix:

    ```bash
    git checkout -b feature/your-feature-name
    ```

3. Set up the development environment using the following command to install the package in editable mode:

    ```bash
    pip install -e .
    ```

    This allows you to test your changes without needing to reinstall the package after each change.

4. Make your changes and ensure that they are fully tested.

5. Commit your changes following the [Conventional Commits](https://www.conventionalcommits.org/) standard. This standard facilitates semantic versioning, improves readability of the commit history, and makes the automation of release notes easier. Example commit message:

   ```bash
   git commit -m "feat: add beta sequence"
   ```

   The commit message contains a type, a scope, and a subject:

   - `type`: This describes the kind of change that this commit is providing. Common types include `feat` (a new feature), `fix` (a bug fix), `docs` (changes to documentation), etc.
   - `scope` (optional): A scope provides additional contextual information and is contained within parenthesis.
   - `subject`: The subject contains a succinct description of the change.

6. Push your branch and create a pull request.

   ```bash
   git push origin feature/your-feature-name
   ```

### Developing with Click

If you're interested in contributing to the `nex` CLI, it's important to be familiar with the Click library. Click uses decorators to associate functions with command-line commands, options, and arguments. Here's a simple example of a Click command:

```python
import click

@click.command()
@click.option('--name', prompt='Your name', help='The person to greet.')
def greet(name):
    click.echo(f'Hello {name}!')

if __name__ == '__main__':
    greet()
```

This code defines a command line tool that asks for the user's name and then greets them. You can create complex CLI commands by stacking multiple decorators and composing commands together.

For more detailed information on how to work with Click when contributing to the `nex` CLI, refer to the [Click documentation](https://click.palletsprojects.com/en/8.0.x/).

### Updating `pyproject.toml`

To update the `pyproject.toml` file with new dependencies or to change existing ones, follow these steps:

1. Locate the `[project.dependencies]` section in the `pyproject.toml` file.

2. To add a new dependency, simply append it to the list, making sure to specify the minimum version you require:

   ```toml
   dependencies = [
       # existing dependencies
       "new-dependency>=1.2.3",
   ]
   ```

3. To update an existing dependency, modify the version number after the `>=` to the new desired version:

   ```toml
   dependencies = [
       "click>=8.1",  # For example, change to "click>=8.2" if updating
       # other dependencies
   ]
   ```

4. After making changes to the `pyproject.toml`, test the project to ensure that the new dependencies are compatible and do not introduce any issues.

## Getting Help

If you encounter any issues or require assistance with the `nex` CLI tool, you can:

- Open an issue on the [GitHub Issue Tracker](https://github.com/nex-team-inc/nexcli/issues).
- Contact the internal support team at the `#team-platform` Slack channel.

Thank you for using or contributing to the `nex` CLI tool. Your efforts help improve everyone's workflow at Nex!
