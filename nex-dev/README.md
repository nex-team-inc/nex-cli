# Nex-Dev

The nex-dev package provides support for developing NEX packages.

## Installation

At the root of a `nexcli` repository, run the following command to install this package:

```BASH
pip install -e nex-dev
```

This will install the `nex-dev` package as an _editable_ package, which means all future update to the code will automatically be made available to the environment.

## Usages

After installation, there is a `nex-dev` executable that can be used to run various utilities.

### Package

To build a package, we can do

```BASH
nex-dev package [-s <package-dir>] build
```

The `-s` flag specifies the root directory of the package. If there is no `pyproject.toml` in that directory, the CLI tool will complain about it and bail out. If the `-s` flag is skipped, it will be assumed to be the current `.` directory.

To upload a package, we can do

```BASH
nex-dev package [-s <package-dir>] upload
```

This will upload the package to the designated internal python repo.

We can also chain them together to be

```BASH
nex-dev package [-s <package-dir>] build upload
```

This will build and upload the package.
