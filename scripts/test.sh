#!/usr/bin/env bash

# pip install pytest==6.2.5 pytest-asyncio==0.16.0 pytest-cov==3.0.0

set -e
set -x

target=${*}
if [ -z "${target}" ]; then
    target=( "tests" )
fi

pytest \
--cov-config=.coveragerc \
--cov=tiny_listener \
--cov-report=term-missing:skip-covered \
--cov-report=html \
--cov-report=xml \
"${target[@]}"
echo "report: $(pwd)/htmlcov/index.html"