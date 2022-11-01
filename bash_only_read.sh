#!/bin/bash
filename=$(ls -lth *.csv | head -n 1 | awk '{print $9}')

python3 only_read.py --conf pointcloud & 
sleep 0.5

counter=$100
while [ $counter -gt 0 ]
do
	data=$(tail -n1 $filename) &
	echo "data = $data";
	counter=$(($counter - 1))
done
#out=$(tail -f $filename ) &
#echo $out
#done
#tail -f 20221101_192348.csv | awk -F',' '{if ($3=="") print ""; else print "True";}'
