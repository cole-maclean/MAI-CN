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
import pickle

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
        simulated_network = scnetwork.SCNetwork(json_graph.node_link_graph(network_data))
    else:
        seed_copy = network_seed.copy()
        simulated_network = build_network(seed_copy,util_params,len(real_network))
    similarity_score,matched_nodes = network_similarity_score(real_network,simulated_network)
    print (similarity_score)
    return -similarity_score 

def network_similarity_score(ref_network,check_network):
    score = 0
    matched_nodes = []
    ref_network_length = len(ref_network)
    for ref_node,ref_data in ref_network.nodes_iter(data=True):
        for check_node,check_data in check_network.nodes_iter(data=True):
            if ref_node[0:4] in geo_tools.gh_expansion(check_node[0:4],2):#check if simulated geohash with geohash twice expanded of precision 4 , if true add to score
                score = score + 1.0/ref_network_length
                matched_nodes.append(check_node)
                break 
    return score,matched_nodes

def build_network(seed_network,utility_params,network_length):
    now_start = datetime.datetime.now()
    start_node = len(seed_network)
    for i in range(len(seed_network),network_length):
        print ("sim network length = " + str(len(seed_network)+1))
        seed_network.expansion_utilities(utility_params)
        if seed_network.expansion_city_ghs:
            new_nodes = {node:data for node,data in seed_network.expansion_cache.items() if node in seed_network.expansion_city_ghs}
            best_node = max(new_nodes, key= lambda x: new_nodes[x][-1])#last value in array
            print (best_node)
        else:
            print ("no expansion cities found at node " + str(i))
            file_name = "simulated_networks/" + str(start_node) + "_" + str(len(seed_network)) + "_" + "_".join([str(param) for param in utility_params.tolist()]) + ".pickle"
            with open(file_name, 'wb') as outfile:
                pickle.dump(seed_network, outfile)
            file_name = "simulated_networks/" + str(start_node) + "_" + str(len(seed_network)) + "_" + "_".join([str(param) for param in utility_params.tolist()]) + ".json"
            with open(file_name, 'w') as outfile:
                json.dump(json_graph.node_link_data(seed_network), outfile)
            return seed_network
        seed_network.add_SC(best_node)
        if len(seed_network[best_node].keys()) == 0:
            print ("added node has no conenctions")
            print (seed_network.expansion_cache[best_node])
    file_name = "simulated_networks/" + str(start_node) + "_" + str(len(seed_network)) + "_" + "_".join([str(param) for param in utility_params.tolist()]) + ".pickle"
    with open(file_name, 'wb') as outfile:
        pickle.dump(seed_network, outfile)
    file_name = "simulated_networks/" + str(start_node) + "_" + str(len(seed_network)) + "_" + "_".join([str(param) for param in utility_params.tolist()]) + ".json"
    with open(file_name, 'w') as outfile:
        json.dump(json_graph.node_link_data(seed_network), outfile)
    now_finish = datetime.datetime.now()
    elapsedTime = now_finish- now_start
    print(elapsedTime / timedelta(minutes=1))
    return seed_network


if __name__ == '__main__':
    with open("simulated_networks/simulation_seed_15000_2_206.pickle", 'rb') as infile:
        seed_net = pickle.load(infile)
    with open("network.json","r") as f:
        network_data = json.load(f)
        G = json_graph.node_link_graph(network_data)
    #current_network = scnetwork.SCNetwork(G)
    #sub_graphs = current_network.all_sub_graphs()
    #seed_net = scnetwork.SCNetwork(sub_graphs[205])
    test_net = scnetwork.SCNetwork(G)
    #test_net = current_network
    args= ([(simulate_networks,(slice(0.8,0.81,0.01),slice(0.22,0.23,0.01)),(test_net,seed_net))])
    #args= ([(simulate_networks,(slice(0,0.1001,0.005),slice(0,101,5)),(test_net,seed_net))])
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
        result_stack = np.stack([*grid, results], -1).reshape(int(len(grid.flatten())/2),-1)
        print (result_stack)
        with open("sim_grid_results.csv",'ba') as f:
            np.savetxt(f,result_stack)


