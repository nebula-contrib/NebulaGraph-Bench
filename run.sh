#!bin/bash

curr_path=$(readlink -f "$(dirname "$0")")
java_prj_path=${curr_path}/util/LdbcGoStep
jmeter_path=$1
jmeter_lib_path=${jmeter_path}/lib/ext
datetime=`date +%Y%m%d_%H%M%S_%N |cut -b1-20`
test_path=${jmeter_path}/${datetime}


jar_path=${java_prj_path}/target/LdbcGoStep-2-jar-with-dependencies.jar
cp -rf ${jar_path} ${jmeter_lib_path}/LdbcGoStep-2-jar-with-dependencies.jar
if [ $? != 0 ] ; then
    echo "cp -rf ${jar_path} ${jmeter_lib_path} failed"
    exit
fi

jmx_path=${curr_path}/ldbc/jmx/go_step.jmx
mkdir ${test_path} &&  cp -rf ${jmx_path} ${test_path}/go_step.jmx

if [ $? != 0 ] ; then
    echo "mkdir ${test_path} &&  cp -rf ${jmx_path} ${test_path}/go_step.jmx"
    exit
fi

perftest_cmd1="${jmeter_path}/bin/jmeter.sh -n -t ${test_path}/go_step.jmx -l ${test_path}/go_step.jtl -j ${test_path}/go_step.log"
perftest_cmd2="${jmeter_path}/bin/jmeter.sh -g ${test_path}/go_step.jtl -o ${test_path}/go_step"
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
