# Horse: A hybrid tool for network reproduction

Horse is a hybrid simulation tool to reproduce network experiments. 
It employs emulation for the control plane and simulation for the data plane.

For now, only the SDN version is available in this repository. It supports controllers
running [OpenFlow 1.3](https://www.opennetworking.org/images/stories/downloads/sdn-resources/onf-specifications/openflow/openflow-spec-v1.3.1.pdf) applications. 

## Instructions for Reproduction of the results from the paper "An SDN-inspired Model for Faster Network Experimentation"

In order to reproduce the results of the paper, it is recommended to create a Virtual Box machine using the Vagrant script provided.
The first step is to download and install Virtual Box for your respective platform.

```
https://www.virtualbox.org/wiki/Downloads
```

Next, download and install vagrant from:

```
https://www.vagrantup.com/downloads.html
```

From now on, you will need a terminal on your respective Operating System (OS). Creating a Virtual Machine (VM)
is the same for every OS. Go to the folder sigsim_pads and execute:

```
vagrant up
``` 

The VM will download and install any dependencies and will also build the tool. 

### Accessing the VM

On Linux or OSX it should be straight forward to login into the VM. Just type:

```
vagrant ssh
```

On Windows you may need to use a solution like [Putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) 
or [Cygwin](https://www.cygwin.com/) to access the VM. For Windows 10 users, you can also [enable the built in ssh client]
(https://fossbytes.com/enable-built-windows-10-openssh-client/). If you decide to use Putty, please follow [this guide](https://www.sitepoint.com/getting-started-vagrant-windows/) 
  
### Running the experiment

There is a script to quickly run our approach and Mininet. It saves the execution time(from Table 2) in a file and
creates the graph from Figure 2. The argument after the script is the number of times each experiment will run. As it can be
seen, for the paper it was used a value of 5 trials per run. 

```
$ cd sigsim_pads
$ ./run_experiment.sh 5
```  

Now check the results for the execution time:

```
$ cd ~/sigsim_pads/graphs
$ vim data/exec_time
```  

The graph is in the pdf format and can be accessed from the computer hosting the Virtual Machine. 
Open the folder sigsim_pads/graphs in your computer and open horse-vs-mn-rate.pdf 

### What the experiment does?

The experiment compares the execution time of both tools and the difference in the the amount of expected traffic 
that should be seem, in the the setup and consideration below:

- Fat Tree topologies with different sizes. The variable K tell the degree of the topology. As it grows, the number of hosts, 
switches and links also increases. (For more information check: https://dl.acm.org/citation.cfm?id=1402967)

- The experiments tests K=6 and K=8. For K=6 there are 48 hosts and for K=8 there are 128 hosts.

- All links have enough bandwidth to not cause loss of traffic. It is important for the comparison.

- The topology is OpenFlow enabled and is controller by an application running Equal-Cost-Multipath-Routing (ECMP).
Because the links are large enough, collision are not an issue and traffic should not be lost.

- Each host sends traffic at the rate of 1Mbps. So for K=6, the expected traffic aggregate is 48Mbs.
For K=8, the expected is 128Mbps.

- The tests are performed an N number of times. The value presented in the graph
is the average of all values observed.

It can be see that when K=8, Mininet cannot cope with the full amount of traffic, because
it needs much more resources than the approach presented in the paper.

## Installing from Scratch

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. 
The installation was only tested on Ubuntu 14.04.

### Prerequisites

Horse is implemented in C with Python binding implemented in Cython.

The current version of this code is compiled on Ubuntu 14.0.4.3 with the following gcc version:
```
gcc version 4.8.4 (Ubuntu 4.8.4-2ubuntu1~14.04.3)
```

Installing Dependencies:

```bash
$ sudo apt-get update && sudo apt-get install build-essential git libevent-dev valgrind ack-grep clang-3.5 bwm-ng -y
$ sudo apt-get install  autoconf libtool build-essential pkg-config python-pip python-dev -y
$ sudo apt-get install libfreetype6-dev libpng12-dev gnuplot -y
$ sudo pip install cython==0.27.3 
```

The connection with OpenFlow controllers needs the installation of a C version from the base part of [Libfluid](http://opennetworkingfoundation.github.io/libfluid/). Consequently, libfluid dependencies are required:

```bash
$ sudo apt-get install autoconf libtool build-essential pkg-config
$ sudo apt-get install libevent-dev 

```

### Installing

The first step is to install the C version of libfluid base from the multi-client branch.

```bash
$ git clone https://github.com/ederlf/libcfluid_base.git
$ cd libcfluid_base
$ git checkout multi-client
$ ./autogen.sh
$ ./configure
$ make
$ sudo make install
$ sudo ldconfig
```

Then compile Horse:

```bash
$ cd sigsim_pads
$ ./boot.sh
$ ./configure
$ make
```

Finally, generate the cython code:

```bash
$ cd sigsim_pads/python
$ python setup.py build_ext --inplace
$ cp ~/sigsim_pads/python/horse.so  ~/sigsim_pads/hedera-ryu/ripl
$ cp ~/sigsim_pads/python/horse.so  ~/sigsim_pads/hedera-ryu/
```

Add the compiled libraries to the LD_LIBRARY_PATH and put it your bashrc so you do not need to perform it every time.

```
$ export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/vagrant/sigsim_pads/.libs:/home/vagrant/sigsim_pads/vendor/loci
$ echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/vagrant/sigsim_pads/.libs:/home/vagrant/sigsim_pads/vendor/loci" >> .bashrc
```

Install Ryu.

```bash
$ cd ~
$ #  Dependencies for ryu
$ sudo apt-get install -y python-routes python-dev
$ sudo pip install -r ~/sigsim_pads/setup/pip-ryu-requires
$ sudo pip install tinyrpc==0.8
$ #  Ryu install
$ cd  ~/sigsim_pads/hedera-ryu/ryu
$ sudo python setup.py install
```

Install Mininet.

```bash
$ cd ~
$ git clone https://github.com/mininet/mininet.git
$ cd mininet
$ git checkout 2.2.2
$ sudo util/install.sh -nV 2.3.0
```

Install matplotlib.

```bash
# This is ugly but could not find a better way to solve it.
# The problem is that matplotlib requires six>=1.10 and the OS version is smaller
# The procedure upgrade pip, removes the OS version and does the same to six.
$ sudo pip install --ignore-installed --upgrade pip==9.0.2
$ sudo apt-get remove python-pip python-six -y
$ sudo pip install --upgrade six==1.11.0
$ sudo pip install matplotlib==2.2.0
```

# Creating a Topology

The code shows how to create a linear topology, composed of N OpenFlow switches and hosts, and schedule pings between all the hosts. 

```python
from horse import *
from random import randint
import sys

def rand_mac():
    return "%02x:%02x:%02x:%02x:%02x:%02x" % (
        randint(0, 255),
        randint(0, 255),
        randint(0, 255),
        randint(0, 255),
        randint(0, 255),
        randint(0, 255)
)

k = int(sys.argv[1]) + 1
hosts = []

topo = Topology()
last_switch = None
for i in range(1, k):
    sw = SDNSwitch("s%s" %i, i)
    h = Host("h%s" % i)
    h.add_port(port = 1, eth_addr = rand_mac(), ip = "10.0.0.%s" % (i), 
               netmask = "255.255.255.0")
    sw.add_port(port = 1, eth_addr = "00:00:00:00:01:00")
    sw.add_port(port = 2, eth_addr = "00:00:00:00:02:00")
    sw.add_port(port = 3, eth_addr = "00:00:00:00:03:00")
    hosts.append(h)
    topo.add_node(h)
    topo.add_node(sw)
    topo.add_link(sw, h, 1, 1, latency = 0) #latency=randint(0,9))
    if last_switch:
        topo.add_link(last_switch, sw, 2, 3)
    last_switch = sw

# Start time for the pings in microseconds
time = 5000000
for i, h in enumerate(hosts):
    for z in range(1, k):
      if z != i + 1:
        # print "10.0.0.%s" % (z)
        h.ping("10.0.0.%s" % (z), time)
        time += 1000000
end_time = 5000000 + (len(hosts) * len(hosts)) * 1000000  
sim = Sim(topo, ctrl_interval = 100000, end_time = end_time, log_level = LogLevels.LOG_INFO)
sim.start()
```

## Running an example

In a future version, the simulator may have capabilities to start a controller, but for now, start the OpenFlow controller of your preference. The application needs to run **OpenFlow 1.3**. 
Example using [Ryu](https://github.com/osrg/ryu) controller.

```bash
$ git clone https://github.com/osrg/ryu.git
$ cd ryu; pip install .
$ ryu-manager ryu/ryu/app/simple_switch_13.py
```

Now, in another window, start the example of a linear topology with 2 hosts and 2 switches:

```bash
$ cd horse
$ python python/linear.py 2
```

The code executes ping between all hosts. You should see some informational logs about the start and conclusion of pings:

```
17:16:31 INFO  src/net/host.c:334: Flow Start time APP 5000000 Execs 1

17:16:31 INFO  src/net/app/ping.c:15: ECHO REQUEST from:a000001 to:a000002

17:16:31 INFO  src/net/app/ping.c:27: ECHO_REPLY ms:19.266 Src:a000001 Dst:a000002
```

## Built With

* [uthash](https://troydhanson.github.io/uthash/) - Hash table for C structures
* [loxigen](https://github.com/floodlight/loxigen) - For generation of OpenFlow structs
* [patricia](https://github.com/jsommers/pytricia) - Used for the routing tables
* [log](https://github.com/rxi/log.c) - Simple logging library
* [json.h](https://github.com/sheredom/json.h) - JSON parser for C and C++

## Authors

* **Eder Leao Fernandes** - *Initial work* - [Personal Page](www.eecs.qmul.ac.uk/~eleao/)

See also the list of [contributors](https://github.com/ederlf/horse/contributors) who participated in this project.

## License

This project is licensed under the BSD License - see the [LICENSE](https://github.com/ederlf/horse/docs/LICENSE) file for details

