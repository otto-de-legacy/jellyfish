#!/usr/bin/env bash
set -e

DOCS_DEPS=false

usage() { echo "Usage: $0 [--doc-deps]" 1>&2;
          echo "Options:"
          echo "	--doc-deps  Includes dependencies to generate docs (ie. Sphinx)."
          exit 1; }

while getopts "h-:" opt; do
  case $opt in
    -)
      case $OPTARG in
        doc-deps)
            DOCS_DEPS=true
            ;;
        *)
            echo "Invalid option: $OPTARG" >&2
            usage
            ;;
      esac
      ;;
    h)
      usage
      ;;
    *)
      echo "Invalid option: -$OPTARG" >&2
      usage
      ;;
  esac
done


echo -e "\x1b[1mPreparing VirtualEnv\x1b[0m"
pip3 install --user virtualenv

python3 -m virtualenv -p python3 venv

./venv/bin/pip3 install -r requirements.txt

if $DOCS_DEPS; then
    echo -e "\x1b[1mInstalling dependencies for docs\x1b[0m"
    ./venv/bin/pip3 install -r docs/requirements.txt
fi
