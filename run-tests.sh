#!/bin/bash

#!/usr/bin/env bash
set -e

./venv/bin/jasmine-ci --browser phantomjs
./venv/bin/nosetests
