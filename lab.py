from lab_app import *
import errno
import json
from multiprocessing import Process

from random import randrange


def read_setup(setup):
    f = open('networks/'+setup+'.json')
    try:
        data = json.load(f)
        return (data.get("nodes"),data.get("bridges"))
    except:
        print("Badly formatted configuration file")

def create_nodes(nodes):
    for node in nodes:
        if not c(node['name']):
            ns_root.register_ns(node['name'],node['image'])
            
def create_bridges(bridges):  
    for bridge in bridges:
        # If 2 adjacencies it is basically a link
        adj = bridge['adjacencies']
        adjcount = len(adj)
        bname = bridge['name']
        if adjcount==2:
            rname = adj[0].split(";")[0]
            name = adj[1].split(";")[0]
 #           print("Connecting " +name + " to " + rname)
            nic = c(name).connect(c(rname),bname, bname)
            r('ip netns exec $name ip link set $bname up')
            r('ip netns exec $rname ip link set $bname up')
        if adjcount > 2:
            # Create switch
  #          print("Setting up bridge for 3 or more nodes")
            ns_root.register_ns(bname, '34334:switch','switch')
            c(bname).enter_ns()
            # Adding bridge in ns
            r('brctl addbr $bname')
            # or r('ip link add name $bname type bridge')
            r('ip link set $bname up')
            r('brctl stp $bname off')
            r('brctl setageing $bname 0')
            r('brctl setfd $bname 0')
            c(bname).exit_ns()
            for node in adj:
                name=node.split(";")[0]
   #             print("Connecting "+bname+" to "+name)
                nic = c(bname).connect(c(name))      
    #            print("Listed nics in " + name + ":")
                for nic in c(name).nics:
                    print(nic)
     #           print("Listed nics in " + bname + ":")
                for nic in c(bname).nics:
                    print(nic)
                r('ip netns exec $bname ip link set $name up')
                r('ip netns exec $name ip link set $bname up') 
                r('ip netns exec $bname brctl addif $bname $name')
                
def ip_address(iprange,host):
    prefix = '.'.join(iprange.split('.')[0:3])
    ipaddress = prefix + "." + str(host)
    return ipaddress

def recode_addresses(bridge):
    iprange = bridge.get("network")
    hostid = 1
    addresstable = []
    gw = bridge.get("gateway")
    gwip=''
    for node in bridge["adjacencies"]:
        name = node.split(";")[0]
        try:
            hostid = int(node.split(";")[1])
        except:
            pass
        addr = {"name" : name, "ip" : ip_address(iprange,hostid) }
        if name == gw:
            gwip = addr["ip"]
        addresstable.append(addr)
        hostid = hostid+1
    return (gw, gwip, addresstable)
            
def set_addresses(bridges):
    # Setting addresses based on json. We assume /24 prefixes and use first available value for gateway unless specified
    print("Setting IP addresses")
    for bridge in bridges:
        bridgename = bridge["name"]
        (gw, gwip, adrtable) = recode_addresses(bridge)
        for node in adrtable:
            name = node["name"]
            ip = node["ip"]
            ip_prefix = ip + "/24"
            r('ip netns exec $name ip addr add $ip_prefix dev $bridgename')
            if (ip != gwip) and gw:
                r('ip netns exec $name ip route add default via $gwip')


def set_internet(inetnode, interface, bridge, ip, gw):
    # Moving external connection to interface in docker config.
    print("Setting up internet via node " + inetnode)
    nic = c(bridge).connect(ns_root)
    
    #ensure network manager doesn't mess with anything
    r('ip netns exec $bridge brctl addif $bridge $nic')
    r('ip netns exec $bridge ip link set $nic up')
    ns_root.enter_ns()

    r('systemctl stop NetworkManager')
    # Connecting root to lab
    print("Connecting localhost to lab")
    r('ip link set $bridge name 34334_lab')
    r('ip link set 34334_lab up')
    r('ip addr add $ip dev 34334_lab')
    # Moving external interface to defined lab node
    r('ip link set $interface netns $inetnode')
    r('ip route add default via $gw')
    
    c(inetnode).enter_ns()
        
    inet_nic = bridge
    r('ip link set $interface up')
    # Setting up NAT as inet node
    r('dhclient $interface')
    r('iptables -t nat -A POSTROUTING -o $interface -j MASQUERADE')
    r('iptables -A FORWARD -i $interface -o $inet_nic -m state --state RELATED,ESTABLISHED -j ACCEPT')
    r('iptables -A FORWARD -i $inet_nic -o $interface -j ACCEPT')
    r('docker exec -ti $inetnode sysctl -w net.ipv4.ip_forward=1')
    # Solving an issue with same MAC addresses. Not nice solution
    r('ip netns exec snort ip link set internal address aa:14:c2:76:80:16')
    r('ip netns exec server ip link set internal address aa:14:c2:76:80:17')
    r('ip netns exec internet ip link set internal address aa:14:c2:76:80:18')
            
                
def setup_firewall(h_if):
    try:
        ns_root.shutdown()
    except:
        print('[*] Did not shutdown cleanly, trying again')
        docker_clean()
    finally:
        docker_clean()
        # Stop IP forwarding on Debian
        r('sysctl -w net.ipv4.ip_forward=0')    
        # Reading network setup
        (nodes,bridges) = read_setup("firewall")
        # Create containers
        print("Start nodes using docker containers")
        create_nodes(nodes)
        # Connecting all dockers in bridges
        print("Interconnect nodes")
        create_bridges(bridges)
        print("Applying IP addressing scheme")
        set_addresses(bridges)  
        # Connecting to internet via lab. Pretty much hardcoded          
        set_internet('internet',h_if,'internal','192.168.1.100/24','192.168.1.1')
        r('docker exec -ti server service nginx start')

def setup_routing(h_if):
    try:
        ns_root.shutdown()
    except:
        print('[*] Did not shutdown cleanly, trying again')
        docker_clean()
    finally:
        docker_clean()
        # Stop IP forwarding on Debian
        r('sysctl -w net.ipv4.ip_forward=0')    
        # Reading network setup
        (nodes,bridges) = read_setup("routing")
        # Create containers
        create_nodes(nodes)
        # Connecting all dockers in bridges
        create_bridges(bridges)
        set_addresses(bridges)  
        # Removing host6, which was constructed just to get the switch.
        # Yes, hardcoding is not nice
        ns_root.ns.remove(c("host5"))
 #       print("Nodes connected to r14")
 #       print(c("r14").nics)
        c("r14").nics.remove("host5")
        # Enable IP forwarding in all routers - yes hardcoding :-(
        for i in range(4):
            k = str(i+1)
            r('docker exec -ti router%s sysctl -w net.ipv4.ip_forward=1' % k)
    
           
        # Select config file and start service in router 1 and 2
        for i in range(2):
            k=str(i+1)
            r('docker exec -ti router%s mv /etc/quagga/ripd%s.conf /etc/quagga/ripd.conf' % (k,k))
            r('docker exec -ti router%s mv /etc/quagga/zebra%s.conf /etc/quagga/zebra.conf' % (k,k))
            r('docker exec -ti router%s service quagga start' % k)
        
