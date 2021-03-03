#! /usr/bin/env bash
curr_path=$(readlink -f "$(dirname "$0")")
java_prj_path=${curr_path}/../../util/LdbcGoStep

if [ $# -lt 1 ] ; then
    echo "Please input jmeter install path"
    exit
else
    path=$1
    echo "jmeter install path is $1"
fi

cd ${java_prj_path}
mvn package
if [ $? != 0 ] ; then
    cd -
    echo "mvn package sucess!"
else
    cd -
    echo "mvn package failed!"
    exit
fi

wget -P $path https://mirrors.bfsu.edu.cn/apache//jmeter/binaries/apache-jmeter-5.4.zip
unzip $path/apache-jmeter-5.4.zip  -d $path/
if [ $? != 0 ] ; then
   echo "install jmeter failed!"
   exit
fi

pip3 install --user -r  ${curr_path}/requirements.txt  -i https://mirrors.aliyun.com/pypi/simple/

if [ $? != 0 ] ; then
   echo "install python3 pkg failed!"
   exit
fi
