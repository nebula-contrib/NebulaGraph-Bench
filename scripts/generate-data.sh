#!/bin/bash
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
DATA_DIR=${PROJECT_DIR}/target/data
source ${SCRIPT_DIR}/env.sh

export HADOOP_HOME=${DATA_DIR}/hadoop-${HADOOP_VERSION}
export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/jre-1.8.0}

mkdir -p ${DATA_DIR}

if [ -d ${HADOOP_HOME} ];then
  echo "Hadoop is existed"
else
  cd ${DATA_DIR} && \
  wget -c   http://archive.apache.org/dist/hadoop/core/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz 
  echo "extract hadoop files"
  tar zxvf hadoop-${HADOOP_VERSION}.tar.gz -C ${DATA_DIR} >  /dev/null
  echo "extract hadoop files done"

fi

export HADOOP_CLIENT_OPTS=${HADOOP_CLIENT_OPTS:-"-Xmx2G"}

if [ -d ${DATA_DIR}/ldbc_snb_datagen ];then
  echo "ldbc_snb_datagen is existed"
else
  cd ${DATA_DIR}  && \
  rm -rf ldbc_snb_datagen && \
  wget https://github.com/ldbc/ldbc_snb_datagen_hadoop/archive/refs/tags/v${LDBC_SNB_DATAGEN_VERSION}.tar.gz && \
  tar -zxvf v${LDBC_SNB_DATAGEN_VERSION}.tar.gz  && \
  mv ldbc_snb_datagen_hadoop-${LDBC_SNB_DATAGEN_VERSION} ldbc_snb_datagen  && \
  cd ldbc_snb_datagen  && \
  cp test_params.ini params.ini
fi


echo "generate data"
cd ${DATA_DIR}/ldbc_snb_datagen && \
# need modify the `scaleFactor` of ldbc_snb
sed -i "s/interactive.*/interactive.${scaleFactor}/g" params.ini && \
# datetime format
sed -i "s/ldbc.snb.datagen.util.formatter.StringDateFormatter.dateTimeFormat.*//g" params.ini && \
echo "ldbc.snb.datagen.util.formatter.StringDateFormatter.dateTimeFormat:yyyy-MM-dd'T'HH:mm:ss.SSS" >> params.ini && \
# set this to the Hadoop 3.2.1 directory
export HADOOP_HOME=${HADOOP_HOME} && \
export LDBC_SNB_DATAGEN_HOME=`pwd`  && \
bash run.sh && \
rm -rf ${DATA_DIR}/test_data && \
mv test_data ${DATA_DIR}/.

echo "Finish"
