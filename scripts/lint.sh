#!/usr/bin/env bash

set -e
set -x

mypy tiny_listener
flake8 tiny_listener tests examples
isort tiny_listener tests examples
black tiny_listener tests examples