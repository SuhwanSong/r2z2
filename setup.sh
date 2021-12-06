#! /bin/bash
set -o xtrace

CUR_DIR="$( cd "$(dirname "$0")" ; pwd -P )"
SRC_DIR=$CUR_DIR/src/
TOL_DIR=$CUR_DIR/tools/

function build_chromium(){
  # Clone depot_tools
  if [ ! -e $TOL_DIR/depot_tools ]; then
    pushd $TOL_DIR
    git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
    popd
  fi
  export PATH="$PATH:$TOL_DIR/depot_tools"

  if [ ! -e $TOL_DIR/wpt ]; then
    pushd $TOL_DIR
    git clone https://github.com/web-platform-tests/wpt.git
    popd
  fi
  # chromium
  mkdir -p chrome && cd chrome

  # Run the fetch tool from depot_tools to check out the code and its dependencies.
  if [ ! -e $CUR_DIR/chrome/src ]; then
    fetch --nohooks chromium

    # Install additional build dependencies
    pushd src
    ./build/install-build-deps.sh
    # Run the hooks
    gclient runhooks
    popd
  fi
}

function download_chromium() {
  pushd $CUR_DIR/chrome
  ver=$1
  python3 ../tools/download_version.py $ver 
  popd
}

# install dep
$CUR_DIR/build/install_dependencies.sh
build_chromium

# test env 1
download_chromium 766000 
download_chromium 784091 
