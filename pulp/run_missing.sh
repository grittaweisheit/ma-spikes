#! /usr/bin/bash

for i in {1..3} 
do
    ./run.sh claim_3_1
    echo "Done with claim_3_1, iteration $i"
    ./run.sh claim_3_3 
    echo "Done with claim_3_3, iteration $i"
done
echo "Done with all iterations"

./run.sh claim_3_1_50
echo "Done with claim_3_1_50"
./run.sh claim_3_3_50
echo "Done with claim_3_3_50"
./run.sh claim_3_1_100
echo "Done with claim_3_1_100"
./run.sh claim_3_3_100
echo "Done with claim_3_3_100"

./run.sh claim_6_1
echo "Done with claim_6_1"
./run.sh claim_6_3
echo "Done with claim_6_3"