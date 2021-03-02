#! /usr/bin/env bash
if [ $# -lt 1 ] ; then
    echo "Please input jmeter install path"
else
    echo "11"
fi
path=$1
wget -P $path https://mirrors.bfsu.edu.cn/apache//jmeter/binaries/apache-jmeter-5.4.zip
unzip $path/apache-jmeter-5.4.zip  -d $path/
pip3 install --user -r  requirements.txt  -i https://mirrors.aliyun.com/pypi/simple/
