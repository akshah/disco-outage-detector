#!/usr/bin/env bash

#declare -a arr=("01" "02" "03" "04" "05" "06" "07" "08" "09" "10" "11" "12")
declare -a arr=("07" "08" "09" "10" "11")
#declare -a arr=("01" "02" "03" "04" "05" "06")

for i in "${arr[@]}"
do
   var="https://atlas.ripe.net/api/v2/probes/archive?day="$1"-"$i"-01 -O probeArchive-"$1$i"01.json"
   wget $var &
done


