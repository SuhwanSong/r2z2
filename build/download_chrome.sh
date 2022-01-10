#! /bin/bash

CUR_DIR="$( cd "$(dirname "$0")" ; pwd -P )"/..

pushd $CUR_DIR/chrome
python3 $CUR_DIR/tools/download_version.py $1
popd
