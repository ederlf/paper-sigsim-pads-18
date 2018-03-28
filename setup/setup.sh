#!/usr/bin/env bash

# Requisites

echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/vagrant/sigsim_pads/.libs:/home/vagrant/sigsim_pads/vendor/loci" >> .bashrc

sudo apt-get update && sudo apt-get install build-essential git libevent-dev valgrind ack-grep clang-3.5 bwm-ng -y
sudo apt-get install  autoconf libtool build-essential pkg-config python-pip python-dev -y
sudo apt-get install libfreetype6-dev libpng12-dev gnuplot -y
sudo pip install cython==0.27.3 

# Test suite
git clone https://github.com/google/cmockery.git && cd cmockery && ./configure && make 
sudo make install
cd ~

#libfluid
git clone https://github.com/ederlf/libcfluid_base.git
cd libcfluid_base
git checkout multi-client
./autogen.sh && ./configure && make
sudo make install
sudo ldconfig

#Compile horse
cd ~/sigsim_pads
./boot.sh
./configure
make

cd ~/sigsim_pads/python
python setup.py build_ext --inplace
cp ~/sigsim_pads/python/horse.so  ~/sigsim_pads/hedera-ryu/ripl/
cp ~/sigsim_pads/python/horse.so  ~/sigsim_pads/hedera-ryu/

cd ~
#  Dependencies for ryu
sudo apt-get install -y python-routes python-dev
sudo pip install -r ~/sigsim_pads/setup/pip-ryu-requires
sudo pip install tinyrpc==0.8
#  Ryu install
cd  ~/sigsim_pads/hedera-ryu/ryu
sudo python setup.py install
    
cd ~
git clone https://github.com/mininet/mininet.git
cd mininet
git checkout 2.2.2
sudo util/install.sh -nV 2.3.0

# This is ugly but could not find a better way to solve it.
# The problem is that matplotlib requires six>=1.10 and the OS version is smaller
# The procedure upgrades pip, removes the OS version and does the same to six.
sudo pip install --ignore-installed --upgrade pip==9.0.2
sudo apt-get remove python-pip python-six -y
sudo pip install --upgrade six==1.11.0
sudo pip install matplotlib==2.2.0
