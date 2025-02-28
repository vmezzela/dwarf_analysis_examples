#!/bin/bash

elf_file=$1
base_path=$2

python3 dwarf_analysis.py --file $elf_file --base_path $base_path |
grep -v '^$' |
grep -v "\[Compilation Unit\]" |
while read func file line addr symtab_idx; do
	if ! sed -n "$line{/$func/p}" $file 2>&1 > /dev/null; then
		echo -e "\033[31m$func NOT found!\033[0m"
		exit 1
	fi
	# --wide option needed otherwise readelf trims the name of the function
	# and break the following script
	if ! readelf --wide -s $elf_file | grep $func | awk -v idx="$symtab_idx" -v addr="$addr" -v name="$func" '
	{
		# Ensure the address from readelf has the same format as input (strip leading zeros)
		readelf_addr = "0x" substr($2, match($2, /[1-9a-fA-F]/))  # Convert 00000000deadbeef -> 0xdeadbeef

		if ($1 == idx":" && readelf_addr == addr && $8 == name) {
			found = 1
		}
	}
	END {
	    if (found == 0) {
		exit 1
	    }
	}
	'; then
		echo -e "\033[31m$func at address $addr NOT found in symtab at index $symtab_idx\033[0m"
		exit 1
	fi
	echo "$func found at $file:$line and in symtab index $symtab_idx"
done
