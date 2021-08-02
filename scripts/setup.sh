#!/bin/bash
# setup dependency tools, including nebula-importer, k6.

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

# Directory of this script
SCRIPT_DIR=$(dirname $(readlink -f "$0"))
# Directory of this project
PROJECT_DIR=$(dirname ${SCRIPT_DIR})
# target data
TEMP_DIR=${PROJECT_DIR}/temp
source ${SCRIPT_DIR}/env.sh

NEBULA_IMPORTER_VERSION=${NEBULA_IMPORTER_VERSION}
NEBULA_XK6_VERSION=${NEBULA_XK6_VERSION}
GOLANG_VERSION=${GOLANG_VERSION}

function setup_nebula_importer(){
  git clone  --branch ${NEBULA_IMPORTER_VERSION} https://github.com/vesoft-inc/nebula-importer ${TEMP_DIR}/nebula-importer
  cd ${TEMP_DIR}/nebula-importer
  make build
  mv nebula-importer ${PROJECT_DIR}/scripts/.
}

function setup_nebula_k6(){
  git clone  --branch ${NEBULA_XK6_VERSION} https://github.com/HarrisChu/xk6-nebula ${TEMP_DIR}/xk6-nebula
  cd ${TEMP_DIR}/xk6-nebula
  make build
  mv k6 ${PROJECT_DIR}/scripts/.
}

function setup_go(){
  # setup go 
  if [ `command -v go` ];then
    echo 'already install golang environment.'
    return 
  fi
  echo "begin install golang environment"
    
  os=`uname | tr "[A-Z]" "[a-z]"`
  case $(uname -m) in
    x86_64)  arch=amd64;;
    aarch64) arch=arm64;;
  esac
  wget -c https://golang.org/dl/go${GOLANG_VERSION}.${os}-${arch}.tar.gz 

  if [ $? != 0 ] ; then
    wget -c https://golang.google.cn/dl/go${GOLANG_VERSION}.${os}-${arch}.tar.gz
    if [ $? !=0 ] ; then
      echo "cannot download golang installation package, please install manually."
      exit 1
    fi
  fi
  tar zxvf go${GOLANG_VERSION}.${os}-${arch}.tar.gz -C ${PROJECT_DIR}  > /dev/null
  export GOPATH=${PROJECT_DIR}/gopath
  export PATH=$PATH:${PROJECT_DIR}/go/bin:${GOPATH}/bin
}

function main(){
  rm -rf ${TEMP_DIR}
  setup_go
  setup_nebula_importer
  setup_nebula_k6
  rm -rf ${TEMP_DIR}
  echo "Finish"

}

main
