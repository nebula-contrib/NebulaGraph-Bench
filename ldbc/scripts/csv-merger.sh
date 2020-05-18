#! /usr/bin/env bash

[[ $# -ge 1 ]] && target=$1 || target=`pwd`
cd $target &>/dev/null

prefixes=( $(ls -1 *[0-9]*.csv 2>/dev/null | sed 's/_[0-9][0-9]*.*//' | sort -u) )

for prefix in ${prefixes[@]}
do
    files=( $(ls -1 ${prefix}_[0-9]* | awk -F_ '{print $0,":",$(NF-1)}' | sort -t: -k2,2 -n | cut -d: -f1) )
    nr_files=${#files[@]}
    lines=$(($(wc -l ${files[@]} | tail -1 | awk '{print $1}') - ${nr_files} + 1))
    echo "Files to merge:"
    printf "%s\n" "${files[@]}"
    echo "Expected # of lines: $lines"

    head -1 ${files[0]} > $prefix.csv
    for f in ${files[@]}
    do
        tail -n+2 $f >> $prefix.csv
    done
    echo "Files merged. Total lines: $(wc -l $prefix.csv)"
    rm -f ${files[@]}
done
