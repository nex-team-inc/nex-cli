#!/bin/bash

rm -rf dist/*
python -m build
python -m twine upload --config-file ../dev/pypirc -r nex-internal-python-repo dist/*
