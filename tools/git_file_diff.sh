#! /bin/bash
CUR_DIR="$( cd "$(dirname "$0")" ; pwd -P )"/..
CHM_DIR=$CUR_DIR/chrome/src

tag=$1
output=$2

pushd $CHM_DIR
git checkout -f $tag
git diff-tree --no-commit-id --name-only -r $tag > $output
#git diff --color --name-status HEAD~ | grep ^A > $output
popd
