#! /usr/bin/bash

file_name=$1

python3 $file_name.py >> runtime/$file_name.out

# vllt in c group laufen lassen, damit es nicht wegen RAM getötet wird