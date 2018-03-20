#!/bin/bash

echo "150" >> ping.txt
for (( k=1; k<=5; k++ ))
do
sudo mn --topo linear,150 --test pingall --controller remote &>> ping.txt
done

echo "200" >> ping.txt
for (( k=1; k<=5; k++ ))
do
sudo mn --topo linear,200 --test pingall --controller remote &>> ping.txt
done

echo "250" >> ping.txt
for (( k=1; k<=5; k++ ))
do
sudo mn --topo linear,250 --test pingall --controller remote &>> ping.txt
done

echo "300" >> ping.txt
for (( k=1; k<=5; k++ ))
do
sudo mn --topo linear,300 --test pingall --controller remote &>> ping.txt
done
