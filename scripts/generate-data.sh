#!/bin/bash

# Directory of this script
SCRIPT_DIR=$(cd "$(dirname "$0")"; pwd)
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
  wget -c http://archive.apache.org/dist/hadoop/core/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz
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
  git clone --branch ${LDBC_SNB_DATAGEN_VERSION} https://github.com/ldbc/ldbc_snb_datagen && \
  cd ldbc_snb_datagen  && \
  cp test_params.ini params.ini
fi


echo "generate data"
cd ${DATA_DIR}/ldbc_snb_datagen && \
# need modify the `scaleFactor` of ldbc_snb
sed -i "s/interactive.*/interactive.${scaleFactor}/g" params.ini && \
# set this to the Hadoop 3.2.1 directory
export HADOOP_HOME=${HADOOP_HOME} && \
export LDBC_SNB_DATAGEN_HOME=`pwd`  && \
sh run.sh && \
mv test_data ${DATA_DIR}/.

echo "Finish"

