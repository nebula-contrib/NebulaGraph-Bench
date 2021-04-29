#! /usr/bin/env bash
curr_path=$(readlink -f "$(dirname "$0")")

casename=""
version=""
jmeter_path=""
test_path=""


while getopts m:c:v:j:t: opt;
do
    case $opt in
        m)   mysqlconf=$OPTARG
             ;;
        c)
             casename=$OPTARG
             ;;
        v)
             version=$OPTARG
             ;;
        j)  
             jmeter_path=$OPTARG
             ;;
        t)
             test_path=$OPTARG
             ;;
    esac
done

if [[ -z $jmeter_path ]] ; then
    echo "Please input jmeter_path"
    exit -1
fi

if [[ -z $test_path ]] ; then
    datetime=`date +%Y%m%d_%H%M%S_%N |cut -b1-20`
    test_path=${jmeter_path}/../${datetime}
else
    datetime=`date +%Y%m%d_%H%M%S_%N |cut -b1-20`
    test_path=${test_path}/${datetime}    
fi

if [ $mysqlconf ] ; then
    if [[ -z $casename ]] ; then
        echo "Please input casename"
        exit -1
    fi

    if [[ -z $version ]] ; then
        echo "Please input nebula version"
        exit -1
    fi
fi

jmx_path=${curr_path}/ldbc/jmx/go_step.jmx

mkdir ${test_path} &&  cp -rf ${jmx_path} ${test_path}/go_step.jmx

if [ $? != 0 ] ; then
    echo "mkdir ${test_path} &&  cp -rf ${jmx_path} ${test_path}/go_step.jmx"
    exit
fi

perftest_cmd1="${jmeter_path}/bin/jmeter.sh -n -t ${test_path}/go_step.jmx -l ${test_path}/go_step.jtl -j ${test_path}/go_step.log  -d ${jmeter_path}"

if [[ -z $mysqlconf ]] ; then
    perftest_cmd2="python3 ${curr_path}/ldbc/scripts/statistics.py -f ${test_path}/go_step.jtl"
else
    perftest_cmd2="python3 ${curr_path}/ldbc/scripts/statistics.py -f ${test_path}/go_step.jtl  -m ${mysqlconf} -c ${casename} -v ${version}"
fi


$perftest_cmd1
if [ $? != 0 ] ; then
    echo "$perftest_cmd1 failed!"
    exit -1
fi


$perftest_cmd2  |  tee  ${test_path}/go_step.statistics

if [ $? != 0 ] ; then

    echo "$perftest_cmd2 failed!"
    exit -1
fi


echo "perf test success, more info in ${test_path}"
