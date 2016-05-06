import importlib
import json
import networkx as nx
from networkx.readwrite import json_graph
import scnetwork
import geo_tools
import geohash
import operator
import numpy as np
from scipy import optimize
from multiprocessing import Pool
import csv
import datetime
from datetime import timedelta

def minimize(args):
    f,rranges,sim_args = args
    resbrute = optimize.brute(f, rranges, args=sim_args, full_output=True,
                              finish=None,disp=99)
    return resbrute

def simulate_networks(util_params,*args):
    print (util_params) 
    real_network,network_seed = args
    seed_copy = network_seed.copy()
    simulated_network = build_network(seed_copy,util_params,len(real_network))
    similarity_score = network_similarity_score(real_network,simulated_network)
    print (similarity_score)
    return -similarity_score 

def network_similarity_score(ref_network,check_network):
    score = 0
    max_distance = 30.0 #max distance (km) away to count as in same city as ref network
    ref_network_length = len(ref_network)
    for ref_node,ref_data in ref_network.nodes_iter(data=True):
        for check_node,check_data in check_network.nodes_iter(data=True):
            if ref_node[0:4] in geohash.expand(check_node[0:4]): #check if we can find the ref_node in the check_network using geohash.expand precision of 4 ie +/-20Kms.
                score = score + 1.0/ref_network_length
                break 
    return score

def build_network(seed_network,utility_params,network_length):
    now_start = datetime.datetime.now()
    start_node = len(seed_network)
    for i in range(len(seed_network),network_length+1):
        print ("sim network length = " + str(len(seed_network)))
        seed_network.expansion_utilities(utility_params)
        if seed_network.expansion_cache:
            new_nodes = {node:data for node,data in seed_network.expansion_cache.items() if node not in seed_network}
            best_node = max(new_nodes, key= lambda x: new_nodes[x][-1])#last value in array
            print (best_node)
        else:
            print ("no expansion cities found at node " + str(i))
            return seed_network
        seed_network.add_SC(best_node)
        del seed_network.expansion_cache[best_node]
    print (str(start_node))
    print (str(len(seed_network)))
    print ("_".join([str(param) for param in utility_params.tolist()]))
    file_name = "generated_networks/" + str(start_node) + "_" + str(len(seed_network)) + "_" + "_".join([str(param) for param in utility_params.tolist()]) + ".json"
    print (file_name)
    with open(file_name, 'w') as outfile:
        json.dump(json_graph.node_link_data(seed_network), outfile)
    now_finish = datetime.datetime.now()
    elapsedTime = now_finish- now_start
    print(elapsedTime / timedelta(minutes=1))
    return seed_network

if __name__ == '__main__':
    with open("network.json","r") as f:
        network_data = json.load(f)
        G = json_graph.node_link_graph(network_data)
    current_network = scnetwork.SCNetwork(G)
    sub_graphs = current_network.all_sub_graphs()
    seed_net = scnetwork.SCNetwork(sub_graphs[180])
    test_net = scnetwork.SCNetwork(sub_graphs[210])
    args= ([(simulate_networks,(slice(0,1001,250),slice(0,1001,250), slice(0,1001,250)),(test_net,seed_net))])
    # args= ([(simulate_networks,(slice(0,2,1),slice(0,0.2,0.1), slice(0,2,1)),(test_net,seed_net)),
    # (simulate_networks,(slice(2,4,1),slice(0.2,0.4,0.1), slice(2,4,1)),(test_net,seed_net)),
    # (simulate_networks,(slice(4,6,1),slice(0.4,0.6,0.1), slice(4,6,1)),(test_net,seed_net)),
    # (simulate_networks,(slice(6,8,1),slice(0.6,0.8,0.1), slice(6,8,1)),(test_net,seed_net)),
    # (simulate_networks,(slice(8,10,1),slice(0.8,1.0,0.1), slice(8,10,1)),(test_net,seed_net)),
    # (simulate_networks,(slice(10,12,1),slice(1.0,1.2,0.1), slice(10,12,1)),(test_net,seed_net))])
    p = Pool(1)
    res = (p.map(minimize,args))
    final_results = []
    for thrd in res:
        grid = thrd[2]
        results = thrd[3]
        result_stack = np.stack([*grid, results], -1).reshape(64,-1)
        with open("sim_grid_results.csv",'ba') as f:
            np.savetxt(f,result_stack)


