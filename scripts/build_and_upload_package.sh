#!/bin/bash

rm -rf dist/*
python -m build
python -m twine upload --config-file ../scripts/pypirc -r nex-internal-python-repo dist/*
