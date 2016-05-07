MAX_RANGE = 346
MAJOR_CITY_POP = 60000
PENETRATION_GH_PRECISION = 4

import networkx as nx
import geo_tools
from operator import itemgetter
import math
import geohash
import numpy as np
import os

POP_DICT = geo_tools.load_pop_dict()
#generate list of unique geohash "squares" of size dictated by GH_PRECISION and use this to build dict of populations grouped by the unique geohash "squares"
sub_ghs = list(set([gh[0:PENETRATION_GH_PRECISION] for gh in list(POP_DICT.keys())]))
sub_pop_dict = {sub_gh:sum([data['population'] for gh,data in POP_DICT.items() if gh[0:PENETRATION_GH_PRECISION] == sub_gh]) for sub_gh in sub_ghs}
tot_pop = sum(list(sub_pop_dict.values()))
major_cities = [city_gh for city_gh,data in POP_DICT.items() if data['population'] >= MAJOR_CITY_POP]

class SCNetwork(nx.Graph):
	def __init__(self,network_data=None):
		nx.Graph.__init__(self,network_data)
		self.expansion_cache = {}
		self.expansion_city_ghs =[]

	#Network Metadata
	def newest_node(self):
		return max(self.nodes(),key=lambda n: int(self.node[n]['SC_index']))

	def reverse_node_lookup(self,SC_indexes):
		nodes = []
		for node,data in self.nodes_iter(data=True):
			if data["SC_index"] in SC_indexes:
				nodes.append(node)
		return nodes 

	def all_sub_graphs(self):
		return ([self.subgraph([node for node,data in self.nodes_iter(data=True)
								   if int(data["SC_index"]) <= node_count + 1])
					 for node_count in range(self.number_of_nodes())])

	def add_SC(self,node_gh):
		if node_gh not in self.nodes():
			node_data = {}
			node_data['SC_index'] = int(self.node[self.newest_node()]["SC_index"]) + 1
			node_data['GPS'] = geohash.decode(node_gh)
			node_data['lat'] = node_data['GPS'][0]
			node_data['lon'] = node_data['GPS'][1]
			node_data['GPS_lon_lat'] = [node_data['lon'],node_data['lat']]
			node_data['population'] = self.SC_population(node_gh)
			node_data['geohash'] = node_gh
			self.add_node(node_gh,{key:node_data[key] for key in node_data.keys()})
			self.add_connections(node_gh)
		return self

	def add_connections(self,src_hash):
		connections = {}
		node_hashes = ([node for node in self.nodes()
						if node[0:2] in geohash.expand(src_hash[0:2])
						and node != src_hash])
		src_GPS = geo_tools.reverse_GPS(geohash.decode(src_hash))
		close_connections = ([{'node':node_gh,
								'directions':geo_tools.get_geohash_directions(src_hash,node_gh)} for node_gh in node_hashes
							if geo_tools.haversine(*src_GPS,*geo_tools.reverse_GPS(geohash.decode(node_gh))) <= MAX_RANGE])
		for connection in close_connections:
			if connection['directions']['distance']/1000 <= MAX_RANGE:
				edge_weight = self.get_edge_weight(src_hash,connection['node'])
				self.add_edge(src_hash,connection['node'],{'weight':edge_weight,'distance':connection['directions']['distance'],
															'steps':connection['directions']['steps'],
															#gets the indx of last node to be added used to determine
															'first_node':str(min(int(self.node[src_hash]["SC_index"]), #order of connection 
															int(self.node[connection['node']]["SC_index"]))),
															'second_node':str(max(int(self.node[src_hash]["SC_index"]), #order of connection 
															int(self.node[connection['node']]["SC_index"]))),
															'lon_lat_1':geo_tools.reverse_GPS(geohash.decode(src_hash)),
															'lon_lat_2':geo_tools.reverse_GPS(geohash.decode(connection['node']))})
		return self

	def get_edge_weight(self,src_hash,connection_hash):
		try:
			pop1 = self.node[src_hash]['population']
			pop2 = self.node[connection_hash]['population']
			return (pop1+pop2)/POP_DICT['total']['population']
		except KeyError as e:
			print(e)
			return 0 

	#population/geographic tools
	def SC_population(self,node_gh):#function uses geohash precision of 3 (ie radius of 73km) and sums population within this radius
		total_close_pop = (sum([data['population'] for gh,data in POP_DICT.items()
					if gh[0:3] in geohash.expand(node_gh[0:3])]))
		return total_close_pop

	#custom defined graph attributes
	def geo_area(self):
		node_GPS_list = [(data["lat"],data["lon"]) for node,data in self.nodes_iter(data=True)]
		sort_lat_GPS = sorted(node_GPS_list,key=itemgetter(0))
		sort_lon_GPS = sorted(node_GPS_list,key=itemgetter(1))
		NS_dist = geo_tools.haversine(-100,sort_lat_GPS[0][0],-100,sort_lat_GPS[-1][0])
		WE_dist = geo_tools.haversine(sort_lon_GPS[0][1],50,sort_lon_GPS[-1][1],50)
		return NS_dist*WE_dist*math.pi

	def largest_subcomponent(self):
		return SCNetwork(max(nx.connected_component_subgraphs(self), key=len))

			#calculate the unique sum total populatition of a network by developing the set of represented geohashes in the network and performing a lookup in the gh_pop_dict
	#for the respective population, normalized by the total population in the gh_pop_dict
	def penetration(self):
		G_sub_ghs = list(set([gh[0:PENETRATION_GH_PRECISION] for gh in self.nodes_iter()]))
		penetrated_sub_ghs = list(set([gh for sub_gh in G_sub_ghs for gh in geohash.expand(sub_gh)]))
		tot_graph_pop = sum([sub_pop_dict[sub_gh] for sub_gh in penetrated_sub_ghs if sub_gh in sub_ghs])
		return tot_graph_pop/tot_pop

	def connectivity(self):
		max_sg = self.largest_subcomponent()#get the maximum sub_graph component
		return max_sg.penetration()

	def robustness(self):
		max_sg = self.largest_subcomponent()#get the maximum sub_graph component
		return nx.node_connectivity(max_sg)

	def efficiency(self):
		max_sg = self.largest_subcomponent()
		if len(max_sg) > 1:
			return (math.sqrt(max_sg.geo_area()/math.pi))/nx.average_shortest_path_length(max_sg)/(MAX_RANGE*3) #Efficieny normalized by the theoretical max efficiency of traveling 3x the max range with 2 SC's
		return 0

	def breadth(self):
		max_sg = self.largest_subcomponent()#get the maximum sub_graph component
		return max_sg.geo_area()/(2762*6425*math.pi) #breadth normalized by maximum theoretical network breadth using extreme North America geographical points

	def density(self):
		max_sg = self.largest_subcomponent()#get the maximum sub_graph component
		G_area = max_sg.geo_area()
		if G_area ==0:
			return 0
		return (len(max_sg)/G_area)*100 #denisty normalized to 1 SC for every 100km^2 in the network

	def SC_expansion_search(self):
		unseen_major_cities = [city_gh for city_gh in major_cities if city_gh not in self.expansion_city_ghs]
		self.expansion_city_ghs = []
		print ("unseen major cities = " + str(len(unseen_major_cities)))
		for node,data in self.nodes_iter(data=True):
			close_city_ghs = set(geo_tools.get_close_ghs(node,unseen_major_cities,2,MAX_RANGE,100))
			for city_gh in close_city_ghs:
				G_sub_ghs = list(set([gh[0:PENETRATION_GH_PRECISION] for gh in self.nodes_iter()]))
				penetrated_sub_ghs = list(set([gh for sub_gh in G_sub_ghs for gh in geohash.expand(sub_gh)]))
				if city_gh not in self.expansion_city_ghs and city_gh[0:PENETRATION_GH_PRECISION] not in penetrated_sub_ghs:
					self.expansion_city_ghs.append(city_gh)
		return self.expansion_city_ghs

	def expansion_utilities(self,util_params):
		#store overall utility values of current network
		expansion_nodes = [gh for gh in self.SC_expansion_search() if gh not in self]
		print ("expansion search cities = " + str(len(expansion_nodes)))
		newest_node = self.newest_node()
		cur_con = self.connectivity()
		cur_eff = self.efficiency()
		#cur_breadth = self.breadth()
		cur_dens = self.density()
		for node in expansion_nodes:
			#this checks to see if the potential expansion nodes utility was previously calculated and if it is within connection distance of the last added node. If it is in the
			#cache and not connected to the newest added node, the cached value of utilities is used. Otherwise, new utilities are calculated. This design forces this function to
			#only work in an incrementally forward expansion search along the network. Otherwise, cache is stale and incorrect.
			if node in list(self.expansion_cache.keys()) and geo_tools.get_close_ghs(node,[newest_node],2,346,0) == []:
				pass #leave util dict for this node unchanged - ie. utilize the cached util values
			else: #add node to network, calculate new incremental utilities and update cache dict
				self.add_SC(node)
				self.expansion_cache[node] = []
				self.expansion_cache[node].append(self.connectivity() - cur_con)
				self.expansion_cache[node].append(self.efficiency() - cur_eff)
				#self.expansion_cache[node].append(self.breadth() - cur_breadth)
				self.expansion_cache[node].append(self.density() - cur_dens)
				node_utility = np.array(self.expansion_cache[node])*np.array(util_params)
				self.expansion_cache[node].append(sum(node_utility))
				self.remove_node(node)
		return self.expansion_cache
