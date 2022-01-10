#! /bin/bash
set -o xtrace

CUR_DIR="$( cd "$(dirname "$0")" ; pwd -P )"
SRC_DIR=$CUR_DIR/src/
TOL_DIR=$CUR_DIR/tools/
DAT_DIR=$CUR_DIR/data

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
    cd src
    ./build/install-build-deps.sh
    # Run the hooks
    gclient runhooks
   
    # Setting up the build
    # gn gen out/Default

    # Build chrome
    # autoninja -C out/Default chrome
  fi
}

function download_chromium() {
  pushd $CUR_DIR/chrome
  ver=$1
  python3 ../tools/download_version.py $ver 
  popd
}

# make directories
mkdir -p $CUR_DIR/firefox
mkdir -p $CUR_DIR/chrome

# install dep
$CUR_DIR/build/install_dependencies.sh

# download versions
pushd $DAT_DIR
python3 bisect-builds.py -a linux64 --use-local-cache
popd

build_chromium

pushd $CUR_DIR/firefox
wget https://github.com/mozilla/geckodriver/releases/download/v0.28.0/geckodriver-v0.28.0-linux64.tar.gz
tar -xf geckodriver-v0.28.0-linux64.tar.gz

mkdir -p $CUR_DIR/chrome
# test env 1
download_chromium 766000 
download_chromium 784091 
pushd $CUR_DIR/firefox
wget https://ftp.mozilla.org/pub/firefox/releases/82.0/linux-x86_64/en-US/firefox-82.0.tar.bz2
tar -xf firefox-82.0.tar.bz2
mv firefox 82.0
ln -s `pwd`/geckodriver `pwd`/82.0/geckodriver
popd

pushd $CUR_DIR
ls chrome/766000/chrome >> testenv1.txt
ls chrome/784091/chrome >> testenv1.txt
popd

# test env 2
download_chromium 870763
download_chromium 905702
pushd $CUR_DIR/firefox
wget https://ftp.mozilla.org/pub/firefox/nightly/2021/08/2021-08-09-21-33-53-mozilla-central/firefox-93.0a1.en-US.linux-x86_64.tar.bz2
tar -xf firefox-93.0a1.en-US.linux-x86_64.tar.bz2
mv firefox 93.0a1
ln -s `pwd`/geckodriver `pwd`/93.0a1/geckodriver
popd

pushd $CUR_DIR
ls chrome/870763/chrome >> testenv2.txt
ls chrome/905702/chrome >> testenv2.txt
popd
