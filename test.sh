#!/bin/bash

file=$1
base_path=$2

python3 dwarf_analysis.py --file $1 --base_path $2 |
grep -v '^$' |
grep -v "\[Compilation Unit\]" |
while read func file line addr; do
	if sed -n "$line{/$func/p}" $file 2>&1 > /dev/null; then
		echo "$func found at $file:$line"
	else
		echo -e "\033[31m$func NOT found!\033[0m"
		exit 1
	fi
done
