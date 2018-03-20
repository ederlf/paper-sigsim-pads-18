#!/bin/bash

TRIALS=$1
echo "Running Paper Approach"
cd ~/sigsim_pads/hedera-ryu
echo "Our Approach" > time.txt
echo "k/switches/hosts Time" >> time.txt
echo -e "4/20/16 \c" >> time.txt
{ TIMEFORMAT="%R"; time ./test_horse.sh $TRIALS 60 4 > /dev/null 2>&1; } 2>> time.txt

echo -e "6/44/54 \c" >> time.txt
{ TIMEFORMAT="%R"; time ./test_horse.sh $TRIALS 60 6 > /dev/null 2>&1; } 2>> time.txt

echo -e "8/80/128 \c" >> time.txt  
{ TIMEFORMAT="%R"; time ./test_horse.sh $TRIALS 60 8 > /dev/null 2>&1; } 2>> time.txt

printf "\n" >> time.txt

echo "Running Mininet"
echo "Mininet" >> time.txt
echo "k/switches/hosts Time" >> time.txt
echo -e "4/20/16 \c" >> time.txt
{ TIMEFORMAT="%R";  time sudo ./test.sh $TRIALS 60 4 > /dev/null 2>&1; } 2>> time.txt

echo -e "6/44/54 \c" >> time.txt
{ TIMEFORMAT="%R"; time sudo ./test.sh $TRIALS 60 6 > /dev/null 2>&1; } 2>> time.txt

echo -e "8/80/128 \c" >> time.txt  
{ TIMEFORMAT="%R"; time sudo ./test.sh $TRIALS 60 8 > /dev/null 2>&1; } 2>> time.txt

echo "Formatting data"
python format_data.py 4
python format_data.py 6
python format_data.py 8

mv time.txt ~/sigsim_pads/graphs/data/exec_time

echo "Compiling graph"
cd ~/sigsim_pads/graphs
make
