# Nex CLI

## Overview

This is a repository for various python packages that constitute to the `nex` CLI command.

## Installation

Please make sure that the installed python version is at least 3.10 to use `nexcli`. If your version of python is not high enough, please upgrade it via `brew`.

To use the nex command, please follow the steps on [notion.so](https://www.notion.so/nexteam/Nex-Internal-CLI-6c3b088888ca43b69e7ec04687673ec4).

## Upgrading

Suppose you are using pipx, upgrading the nex command can be done via

```bash
pipx upgrade nexcli
```

## Contributing

Clone and set up the repo for contributions:

```bash
git clone https://github.com/nex-team-inc/nexcli.git
git checkout -b feature/your-feature-name
pip3 install -e .
```

Test changes, follow [Conventional Commits](https://www.conventionalcommits.org/) for messages, and submit pull requests.

```bash
git commit -m "feat: add beta sequence"
```

The commit message contains a type, a scope, and a subject:

- `type`: This describes the kind of change that this commit is providing. Common types include `feat` (a new feature), `fix` (a bug fix), `docs` (changes to documentation), etc.
- `scope` (optional): A scope provides additional contextual information and is contained within parenthesis.
- `subject`: The subject contains a succinct description of the change.

## Development

Other than the `scripts` folder, the various folders under the root directory are individual packages. All these packages should be hosted in the `nex-internal-python-repo`. For general users, they can fetch all these packages through the virtual repository `nex-python-repo` setup in the installation steps above.

To deal with the internal repo, we need to setup authentication and what not. For that, we need to install the `keyring` and other dependencies. At root level, there is already a `.envrc` file that, together with the [direnv](https://direnv.net/) tools, creates a virtual environment for package development. After activating `direnv`, we can install all common requirements through

```bash
pip install -r requirements.txt
```

### Maintaining packages

Since each folder is essentially a python package (with their own `pyproject.toml`), each of them can be treated as one. As a standard practice, we can install them as editable package via

```bash
pip install -e <path>
```

For CLI, they are installed via `pipx`. We can still use the same trick

```bash
pipx install --editable <path>
```

If the executable is already installed, and we want to temporarily replace it with an editable version, we can do

```bash
pipx inject --editable <executable> <path>
```

When all editing is done, and the package version is updated, we can build and upload the package through

```bash
../scripts/build_and_upload_package.sh
```

To undo the editable package, one can reinstall the package again. For `pipx`, we simply need to inject again:

```bash
pipx inject <executable> <path>
```
