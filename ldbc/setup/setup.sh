#! /usr/bin/env bash
curr_path=$(readlink -f "$(dirname "$0")")
java_prj_path=${curr_path}/../../util/LdbcGoStep

if [ $# -lt 1 ] ; then
    echo "Please input jmeter install path"
    exit
else
    jmeter_install_path=$1
    echo "jmeter install path is $1"
fi

cd ${java_prj_path}
mvn package
if [ $? != 0 ] ; then
    cd -
    echo "mvn package failed!"
    exit
fi
 
cd -

wget -P $jmeter_install_path https://mirrors.bfsu.edu.cn/apache/jmeter/binaries/apache-jmeter-5.4.zip
unzip ${jmeter_install_path}/apache-jmeter-5.4.zip  -d $jmeter_install_path
if [ $? != 0 ] ; then
   echo "install jmeter failed!"
   exit
fi

jar_path=${java_prj_path}/target/LdbcGoStep-2-jar-with-dependencies.jar
jmeter_lib_path=${jmeter_install_path}/apache-jmeter-5.4/lib/ext
cp -rf ${jar_path} ${jmeter_lib_path}/LdbcGoStep-2-jar-with-dependencies.jar
if [ $? != 0 ] ; then
    echo "cp -rf ${jar_path} ${jmeter_lib_path} failed"
    exit
fi


pip3 install --user -r  ${curr_path}/requirements.txt  -i https://mirrors.aliyun.com/pypi/simple/

if [ $? != 0 ] ; then
   echo "install python3 pkg failed!"
   exit
fi
