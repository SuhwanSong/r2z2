#! /bin/bash
# ref: https://gitlab.com/noencoding/OS-X-Chromium-with-proprietary-codecs/-/wikis/List-of-all-gn-arguments-for-Chromium-build
# set -o xtrace

CUR_DIR="$( cd "$(dirname "$0")" ; pwd -P )"/..
CHM_DIR=$CUR_DIR/chrome/src
TOL_DIR=$CUR_DIR/tools/
export PATH="$PATH:$TOL_DIR/depot_tools"

export CCACHE_CPP2=yes
export CCACHE_SLOPPINESS=time_macros
export PATH=$CHM_DIR/third_party/llvm-build/Release+Asserts/bin:$PATH

GIT_VER=$1
TAGS="tags/"
TAGS=$2

pushd $CHM_DIR
git checkout -f $TAGS$GIT_VER || exit 1
git reset --hard
COMMIT_DATE=$(git log -n 1 --pretty=format:%ci)

pushd $TOL_DIR/depot_tools
git checkout $(git rev-list -n 1 --before="$COMMIT_DATE" master) || exit 1
export DEPOT_TOOLS_UPDATE=0
git clean -ffd
popd

echo $PWD

gclient sync -D --force --reset
./build/install-build-deps.sh

gclient runhooks

gn gen out/Release
cp $CUR_DIR/build/args.gn out/Release

gn gen out/Release
autoninja -C out/Release chrome

rm -rf out/$GIT_VER
cp -r out/Release out/$GIT_VER
#VER=`out/$GIT_VER/chrome --version`


gn gen out/chromedriver
autoninja -C out/chromedriver chromedriver

rm -rf out/$GIT_VER/chrd
cp -r out/chromedriver out/$GIT_VER/chrd

#TMP1=($VER)
#TMP2=${TMP1[1]}
#VER_NUM=(${TMP2//./ })
#VER=${VER_NUM[0]}

#cp $CUR_DIR/build/$VER/chromedriver out/$GIT_VER/ 

mkdir $CUR_DIR/chrome/$BRV
ln -s `pwd`/out/$GIT_VER/chrome $CUR_DIR/chrome/$BRV/chrome
ln -s `pwd`/out/$GIT_VER/chrd/chromedriver $CUR_DIR/chrome/$BRV/chromedriver
