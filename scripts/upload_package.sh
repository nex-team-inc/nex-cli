#!/bin/bash

python -m twine upload --config-file ../scripts/pypirc -r nex-internal-python-repo dist/*
