from horse import *

sw1 = SDNSwitch(42)
# sw2 = SDNSwitch(42)
# sw3 = SDNSwitch(42)

h1 = Host()
h2 = Host()

sw1.add_port(1, "00:00:00:00:01:00")
sw1.add_port(2, "00:00:00:00:02:00")

h1.add_port(1, "00:00:00:00:00:01", ip = "10.0.0.1", netmask = "255.255.255.0" )
h2.add_port(1, "00:00:00:00:00:02", ip = "10.0.0.2", netmask = "255.255.255.0")

start_time = 1000000

h1.ping("10.0.0.2", start_time)

topo = Topology()
topo.add_node(sw1)
topo.add_node(h1)
topo.add_node(h2)
topo.add_link(sw1, h1, 1, 1)
topo.add_link(sw1, h2, 2, 1)

sim = Sim(topo)
sim.start()
