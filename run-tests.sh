#!/bin/bash

#!/usr/bin/env bash
set -e
if [ -d ./venv ]; then
  VENV=./venv/bin/
  PYTHON=${VENV}python3
else
  PYTHON=python3
fi
${VENV}jasmine-ci --browser phantomjs
${VENV}nosetests
