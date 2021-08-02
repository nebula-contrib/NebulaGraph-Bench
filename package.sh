#! /bin/bash

set -e
shopt -s expand_aliases

# cross-OS compatibility (greadlink, gsed, zcat are GNU implementations for OS X)
[[ `uname` == 'Darwin' ]] && {
	which greadlink gsed gzcat > /dev/null && {
		alias readlink=greadlink sed=gsed zcat=gzcat
	} || {
		echo 'ERROR: GNU utils required for Mac. You may use homebrew to install them: brew install coreutils gnu-sed'
		exit 1
	}
}

PROJECT_DIR=$(dirname $(readlink -f "$0"))
cd ${PROJECT_DIR}


pip3 install --user -r requirements.txt
pip3 install --user -r requirements_dev.txt

# compile go tools
./scripts/setup.sh

# package python code
pyinstaller -D nebula-bench.spec

# tar
cd dist
tar zcvf nebula-bench.tgz nebula-bench/*