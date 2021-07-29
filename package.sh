#! /bin/bash

set -e

pip3 install --user -r requirements.txt
pip3 install --user -r requirements_dev.txt

# compile go tools
/bin/bash scripts/setup.sh

# package python code
pyinstaller -D nebula-bench.spec

# tar
cd dist
tar zcvf nebula-bench.tgz nebula-bench/*