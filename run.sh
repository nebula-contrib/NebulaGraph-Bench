#! /usr/bin/env bash
curr_path=$(readlink -f "$(dirname "$0")")


if [ $# -lt 1 ] ; then
    echo "Please input jmeter_path and test path(default is jmeter_path/..)"
    exit
elif [ $# -eq 1 ] ; then
    jmeter_path=$1
    datetime=`date +%Y%m%d_%H%M%S_%N |cut -b1-20`
    test_path=${jmeter_path}/../${datetime}
    echo "jmeter_path is $jmeter_path"
    echo "test_path is $test_path"
else
    jmeter_path=$1
    datetime=`date +%Y%m%d_%H%M%S_%N |cut -b1-20`
    test_path=$2/${datetime}
    echo "jmeter path is $jmeter_path"
    echo "test path is $test_path"
fi

jmx_path=${curr_path}/ldbc/jmx/go_step.jmx

mkdir ${test_path} &&  cp -rf ${jmx_path} ${test_path}/go_step.jmx

if [ $? != 0 ] ; then
    echo "mkdir ${test_path} &&  cp -rf ${jmx_path} ${test_path}/go_step.jmx"
    exit
fi

perftest_cmd1="${jmeter_path}/bin/jmeter.sh -n -t ${test_path}/go_step.jmx -l ${test_path}/go_step.jtl -j ${test_path}/go_step.log  -d ${jmeter_path}"
perftest_cmd2="${jmeter_path}/bin/jmeter.sh -g ${test_path}/go_step.jtl -o ${test_path}/go_step -j ${test_path}/go_step.log  -d ${jmeter_path}"
perftest_cmd3="python3 ${curr_path}/ldbc/scripts/statistics.py ${test_path}/go_step.jtl"

$perftest_cmd1
if [ $? != 0 ] ; then
    echo "$perftest_cmd1 failed!"
    exit
fi


$perftest_cmd2

if [ $? != 0 ] ; then

    echo "$perftest_cmd2 failed!"
    exit
fi

$perftest_cmd3   |  tee  ${test_path}/go_step.statistics

if [ $? != 0 ] ; then

    echo "$perftest_cmd3 failed!"
    exit
fi


echo "perf test success, more info in ${test_path}"
