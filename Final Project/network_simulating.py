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
import os

def minimize(args):
    f,rranges,sim_args = args
    resbrute = optimize.brute(f, rranges, args=sim_args, full_output=True,
                              finish=None,disp=99)
    return resbrute

def simulate_networks(util_params,*args):
    print (util_params)
    real_network,network_seed = args
    start_node = len(network_seed)
    end_node = len(real_network)
    cached_networks = os.listdir("simulated_networks/")
    file_name = str(start_node) + "_" + str(end_node) + "_" + "_".join([str(param) for param in util_params.tolist()]) + ".json"
    if file_name in cached_networks:
        with open("simulated_networks/" + file_name,"r") as f:
            network_data = json.load(f)
            print ("network cache succesfully loaded")
        return scnetwork.SCNetwork(json_graph.node_link_graph(network_data))
    seed_copy = network_seed.copy()
    simulated_network = build_network(seed_copy,util_params,len(real_network))
    similarity_score = network_similarity_score(real_network,simulated_network)
    print (similarity_score)
    return -similarity_score 

def network_similarity_score(ref_network,check_network):
    score = 0
    ref_network_length = len(ref_network)
    for ref_node,ref_data in ref_network.nodes_iter(data=True):
        for check_node,check_data in check_network.nodes_iter(data=True):
            if ref_node[0:4] in geohash.expand(check_node[0:4]):#check if simulated geohash with geohash expanision of precision 4 (ie. +/-20km), if true add to score
                score = score + 1.0/ref_network_length
                break 
    return score

def build_network(seed_network,utility_params,network_length):
    now_start = datetime.datetime.now()
    start_node = len(seed_network)
    for i in range(len(seed_network),network_length):
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
    file_name = "simulated_networks/" + str(start_node) + "_" + str(len(seed_network)) + "_" + "_".join([str(param) for param in utility_params.tolist()]) + ".json"
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
    args= ([(simulate_networks,(slice(0,101,20),slice(0,101,20), slice(0,101,20)),(test_net,seed_net))])
    # args= ([(simulate_networks,(slice(0,200,50),slice(0,200,50), slice(0,200,50)),(test_net,seed_net)),
    # (simulate_networks,(slice(200,400,50),slice(200,400,50), slice(200,400,50)),(test_net,seed_net)),
    # (simulate_networks,(slice(400,600,50),slice(400,600,50), slice(400,600,50)),(test_net,seed_net)),
    # (simulate_networks,(slice(600,800,50),slice(600,800,50), slice(600,800,50)),(test_net,seed_net)),
    # (simulate_networks,(slice(800,1000,50),slice(800,1000,50), slice(800,1000,50)),(test_net,seed_net)),
    # (simulate_networks,(slice(1000,1200,50),slice(1000,1200,50), slice(1000,1200,50)),(test_net,seed_net))])
    p = Pool(1)
    res = (p.map(minimize,args))
    final_results = []
    for thrd in res:
        grid = thrd[2]
        results = thrd[3]
        result_stack = np.stack([*grid, results], -1).reshape(int(len(grid.flatten())/3),-1)
        with open("sim_grid_results.csv",'ba') as f:
            np.savetxt(f,result_stack)


