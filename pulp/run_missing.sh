#! /usr/bin/bash

for i in {1..3} 
do
    ./run.sh room_3rooms_1b_fs
    ./run.sh room_3rooms_1b_ls
    ./run.sh room_3rooms_2b_fs
    ./run.sh room_3rooms_2b_ls

    ./run.sh room_1-1-4_1b_fs
    ./run.sh room_1-1-4_1b_ls
    ./run.sh room_1-1-4_2b_fs
    ./run.sh room_1-1-4_2b_ls

    ./run.sh room_3-3-0_1b_fs
    ./run.sh room_3-3-0_2b_fs

    ./run.sh claim_3_1
    ./run.sh claim_3_3

    echo "iteration $i"
done

echo "XXX Done with all iterations"

./run.sh claim_6_1
echo "Done with claim_6_1"

./run.sh claim_3_1_50
echo "Done with claim_3_1_50"
./run.sh claim_3_3_50
echo "Done with claim_3_3_50"
./run.sh claim_3_1_100
echo "Done with claim_3_1_100"
./run.sh claim_3_3_100
echo "Done with claim_3_3_100"

./run.sh room_3rooms_2b_fs_50
echo "Done with room_3rooms_2b_fs_50"
./run.sh room_3rooms_2b_ls_50
echo "Done with room_3rooms_2b_ls_50"

./run.sh room_3rooms_2b_fs_100
echo "Done with room_3rooms_2b_fs_100"
./run.sh room_3rooms_2b_ls_100
echo "Done with room_3rooms_2b_ls_100"

./run.sh room_1-1-4_2b_ls_50
echo "Done with room_1-1-4_2b_ls_50"
./run.sh room_1-1-4_2b_ls_100
echo "Done with room_1-1-4_2b_ls_100"

echo "XXX Done with all a little longer stuff"

./run.sh room_3-3-0_1b_ls
echo "Done with room_3-3-0_1b_ls"

./run.sh room_3-3-0_2b_ls
echo "Done with room_3-3-0_2b_ls"

./run.sh claim_6_3
echo "Done with claim_6_3"