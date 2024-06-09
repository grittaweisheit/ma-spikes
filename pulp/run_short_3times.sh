#! /usr/bin/bash

for i in 1 2 3
do
    ./run.sh room_3rooms
    ./run.sh room_3rooms_1builder
    ./run.sh room_3rooms_fasterShower
    ./run.sh room_3rooms_1builder_fasterShower

    ./run.sh room_6rooms
    ./run.sh room_6rooms_fasterShower
    ./run.sh room_6rooms_3-3
    ./run.sh room_6rooms_fasterShower_3-3
    ./run.sh room_6rooms_1builder
    ./run.sh room_6rooms_1builder_fasterShower
    ./run.sh room_6rooms_1builder_3-3
    ./run.sh room_6rooms_1builder_fasterShower_3-3

    ./run.sh room_3rooms_50
    ./run.sh room_3rooms_100
    ./run.sh room_6rooms_50
    ./run.sh room_6rooms_100

    ./run.sh claim_3_1
    ./run.sh claim_3_1_50
    ./run.sh claim_3_1_100
    ./run.sh claim_3_3
    ./run.sh claim_3_3_50
    ./run.sh claim_3_3_100
done
