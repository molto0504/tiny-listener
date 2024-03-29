#!/usr/bin/env bash

set -e
set -x

paths=( "tiny_listener" "tests" "examples")

isort \
--combine-as \
--profile black \
--project=tiny_listener \
"${paths[@]}"

autoflake \
--recursive \
--in-place \
--remove-all-unused-imports \
"${paths[@]}"

black \
--target-version=py38 \
--line-length=120 \
"${paths[@]}"

flake8 \
--ignore=E203,E501,W503 \
--max-line-length=120 \
"${paths[@]}"

mypy \
--ignore-missing-imports \
--disallow-untyped-defs \
--follow-imports=silent \
tiny_listener
