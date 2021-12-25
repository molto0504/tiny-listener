#!/usr/bin/env bash

set -e
set -x

mypy tiny_listener
flake8 tiny_listener tests
isort tiny_listener tests
black tiny_listener tests