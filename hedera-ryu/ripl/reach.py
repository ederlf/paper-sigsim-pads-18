import sys
from horse import *
from horsedctopo import FatTreeTopo

topo = FatTreeTopo(k=int(sys.argv[1]))

hosts = topo.hosts()
# print len(topo.layer_nodes(topo.LAYER_EDGE))
# print len(topo.switches())
# print len(hosts)
# print edge[0], h, topo.port(edge[0], h)
# print topo.node_info[h]["mac"]
time = 10000000
n = 0
for i, h in enumerate(hosts):
    host1 = topo.nodes[h]
    for h2 in hosts:
        if h != h2:
            h2_ip = topo.node_info[h2]["ip"]
            host1.ping(h2_ip, time)
            n += 1
            time += 1000000
#             # break
#     # break
# print "Nr of flow %s" % n
print n
end_time = time + n * 1000000
print end_time
sim = Sim(topo, ctrl_interval = 20000, end_time = end_time)
sim.start()
