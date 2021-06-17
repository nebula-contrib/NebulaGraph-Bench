#!/bin/bash

# Directory of this script
SCRIPT_DIR=$(cd "$(dirname "$0")"; pwd)
# Directory of this project
PROJECT_DIR=$(dirname ${SCRIPT_DIR})
# target data
DATA_DIR=${PROJECT_DIR}/target/data

source ${SCRIPT_DIR}/env.sh

# merge data
for folder in dynamic static;do
    cd ${DATA_DIR}/test_data/social_network/${folder}
    for f in $(ls -1 *_0_0.csv);
    do

    dst=$(echo $f | sed 's/_0_0//')
    name=$(echo $dst | sed 's/.csv$//')
    mv $f $dst
    head $dst > ${name}_header.csv
    # delete first row
    sed -i '1d' $dst
    done

done

echo "Finish"