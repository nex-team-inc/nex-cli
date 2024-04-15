#!/bin/bash

python -m twine upload --config-file ../dev/pypirc -r nex-internal-python-repo dist/*
