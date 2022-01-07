#!/usr/bin/env bash

set -e
set -x

pytest --cov-config=.coveragerc --cov=tiny_listener --cov-report=term-missing:skip-covered --cov-report=html --cov-report=xml tests "${@}"