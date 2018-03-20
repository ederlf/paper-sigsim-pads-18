# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

class IP_LBalancer(object):
    def __init__(self, config):
        super(IP_LBalancer, self).__init__()
        
    def init_match(self, match_bytes):
        
        self.match_list = []

        # fill bytearray with match
        # string like '00000011' or
        # int from 0 to 255
        byte_array = bytearray(len(match_bytes))
        for i in range(len(match_bytes)): 
            val = match_bytes[i]
            if isinstance(val, str):
                byte_array[i] = int(val, 2)
            elif isinstance(val,int):
                byte_array[i] = val

        # set for every match
        # [set([0]), set([0]), set([0]), set([0, 32, 64, 96])]
        # match_bytes [0, 0, 0, "01100000"]
        set_array = []
        for i in range(len(byte_array)):
            new_set = set([])
            for j in range(0, 255):
                new_set.add(byte_array[i] & j) # logic AND
            set_array.append(new_set)


        ##todo -----------------------------------------
        # idea to build matches from the different bytes 
        allset = set([])
        for index, value in enumerate(set_array):
            #print(index, value)
            if len(value) > 1:
                setlist = list(value)
        for set_elem in setlist:
            var = (index+1-len(setlist))*256
            if (var == 0): 
                var=1
            allset.add(set_elem * var)
        #debug print
        #print ("allset: %s ") % allset -----------------

        # look only on the 4th byte
        for match in set(set_array[3]):
            self.match_list.append(match)
        return self.match_list


    def set_core_match(self, cores, match_list):
        self.id_matcher = {}
        
        # link every core to a match
        for index, core in enumerate(cores):
            core_id = cores[core] # index or core
            elem = match_list[index%len(match_list)]
            self.id_matcher.update({core_id:elem})

    def get_ip_match(self, match_id, field):
        METADATA_MASK = 0xffffffff
        ETH_TYPE_IP = 0x0800
        metadata = [match_id, METADATA_MASK]
        mask = self.get_ip_network()
        checked_field = self.check_possibile_fields(field)
        ipv4 = 0

        if match_id in self.id_matcher:
            #return decimal mask
            ipv4 = (self.id_matcher[match_id], mask)
        match = {"eth_type": ETH_TYPE_IP, checked_field: ipv4}
        return match, metadata

    # -----------------------------------------------------------------------------------

    def init_multi_match(self, match_byte1, match_byte2):
        return self.init_match(match_byte1), self.init_match(match_byte2)


    def set_core_multi_match(self, cores, match_list):
        self.id_matcher = {}

        if (len(match_list) == 2):
            subsets = self.get_subsets(match_list)
        else:
            subsets = match_list
        
        # link every core to a match
        for index, core in enumerate(cores):
            core_id = cores[core]
            elem = subsets[index%len(subsets)]
            self.id_matcher.update({core_id:elem})
       
    def get_ip_multi_match(self, match_id, fields):
        METADATA_MASK = 0xffffffff
        ETH_TYPE_IP = 0x0800
        metadata = [match_id, METADATA_MASK]
        mask = self.get_ip_network()

        ipv4 = 0
        match = {"eth_type": ETH_TYPE_IP}

        for index, field in enumerate(fields):
            checked_field = self.check_possibile_fields(field)
            
            if match_id in self.id_matcher:
                #return decimal tupel
                ipv4 = self.id_matcher[match_id]
                match.update({checked_field : (ipv4[index], mask[index])})

        return match, metadata

  # -----------------------------------------------------------------------------------

    # need for mask
    def get_ip_network(self):
        return self.id_matcher[max(self.id_matcher, key=self.id_matcher.get)]

    # need for field_check
    def check_possibile_fields(self, field):
        ipv4_fields = ["ipv4_src", "ipv4_dst"]
        if field in ipv4_fields:
            return field
        else:
            return 0

    # todo - build for multi matches > 2
    def get_subsets(self, sets):
        new_set = set([])
        for elem1 in sets[0]:
            for elem2 in sets[1]:
                elem = (elem1,elem2)
                new_set.add(elem)
        return list(new_set)

    def get_flow_mod(self):
        return self.flow_mods

    def lb_policy(self, edge_core):
        for edge in edge_core:
            self.edge_out_ports.setdefault(edge, {})
            core = random.choice([x for x in edge_core[edge]])
            self.edge_out_ports[edge] = (core, edge_core[edge][core])

    def lb_action(self, edge):
        return self.edge_out_ports[edge]

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.pktin = 0

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        #print "Sendind default flow " + str(datapath.id)
        self.add_flow(datapath, 0, match, actions)
 
        self.send_port_stats_request(datapath);


    def send_port_stats_request(self, datapath):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        req = ofp_parser.OFPPortStatsRequest(datapath, 0, ofp.OFPP_ANY)
        datapath.send_msg(req)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)


    def install_load_balancer(self, rule_type):
        
        # multi check
        match_byte1 = [0, 0, 0, "00000001"]
        match_byte2 = [0, 0, 0, "00000001"]
        
        # create id_matches - init core multi match with id_matches
        id_matcher1, id_matcher2 = self.lbal.init_multi_match(match_byte1, match_byte2)
        self.lbal.set_core_multi_match(self.config.cores, [id_matcher1, id_matcher2])

        # Rule for every Edge
        for edge in self.config.edge_core:
            # Rule to every Core
            for core in self.config.cores:            
                # Decision for Match is core_id
                core_id = self.config.cores[core]

                # multi check field(s)
                match, metadata = self.lbal.get_ip_multi_match(core_id, ['ipv4_src','ipv4_dst'])

                # Build Instruction Meta-Information and Goto-Table
                instructions = {"meta": metadata, "fwd": ["umbrella-edge"]}

                # Send for every Core to every Edge
                self.fm_builder.add_flow_mod("insert", rule_type, LB_PRIORITY, match, instructions, self.config.dpid_2_name[edge]) 
            # Need to handle VNH MACS. 
            # TODO: Add group to support fast failover.
            match = {"eth_type": ETH_TYPE_ARP}
            # Picking the last core from the last loop. Should be replaced 
            # with a group later
            metadata = [self.config.cores[core], METADATA_MASK] 
            instructions = {"meta": metadata, "fwd": ["umbrella-edge"]}
            self.fm_builder.add_flow_mod("insert", rule_type, LB_PRIORITY, match, instructions, self.config.dpid_2_name[edge]) 

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']


        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
