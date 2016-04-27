import networkx as nx
import geo_tools

class SCNetwork(nx.Graph):
    def __init__(self,network_data=None):
        nx.Graph.__init__(self,network_data)

    def geo_area(self):
        node_GPS_list = [(data["lat"],data["lon"]) for node,data in self.nxG.nodes_iter(data=True)]
        sort_lat_GPS = sorted(node_GPS_list,key=itemgetter(0))
        sort_lon_GPS = sorted(node_GPS_list,key=itemgetter(1))
        NS_dist = geo_tools.haversine(sort_lat_GPS[0][0],0,sort_lat_GPS[-1][0],0)
        WE_dist = geo_tools.haversine(sort_lon_GPS[0][1],0,sort_lon_GPS[-1][1],0)
        return NS_dist*WE_dist*math.pi