from math import radians, cos, sin, asin, sqrt
import json
import configparser
import googlemaps
import time
import geohash
import os

config = configparser.ConfigParser()
config.read("config.ini")
API_key = config['Keys']['google_API']
gmaps = googlemaps.Client(key=API_key)

with open("google_directions_cache.json","r") as f:
    google_directions_cache = json.load(f)

def load_pop_dict():
    with open('populations.json', 'r') as f:
        p_dict = json.load(f)
    return p_dict

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6367 * c
    return km
#reverse lon/lat positions of a GPS tuple
def reverse_GPS(GPS):
    return [GPS[1],GPS[0]]

def get_geohash_directions(gh_A,gh_B):
    with open("google_directions_cache.json","r") as f:
        try:
            google_directions_cache = json.load(f)
        except ValueError:
            print ("cache in use or corrupted")
            GPS_A = geohash.decode(gh_A)
            GPS_B = geohash.decode(gh_B) 
            directions_result = gmaps.directions(GPS_A,
                                                 GPS_B,
                                                 mode="driving")
            connection_data =({'distance':directions_result[0]['legs'][0]['distance']['value'],
                               'steps':len(directions_result[0]['legs'][0]['steps'])})
            return connection_data
    sorted_hashes = sorted([gh_A,gh_B])
    connection_key = sorted_hashes[0] + sorted_hashes[1]
    if connection_key in list(google_directions_cache.keys()):
        connection_data = google_directions_cache[connection_key]
    else:
        GPS_A = geohash.decode(gh_A)
        GPS_B = geohash.decode(gh_B) 
        directions_result = gmaps.directions(GPS_A,
                                             GPS_B,
                                             mode="driving")
        connection_data =({'distance':directions_result[0]['legs'][0]['distance']['value'],
                           'steps':len(directions_result[0]['legs'][0]['steps'])})
        google_directions_cache[connection_key] = connection_data
        while int(os.stat("google_directions_cache.json").st_size) == 0:
            time.sleep(0.005)
        with open("google_directions_cache.json","w") as f:
            try:
                json.dump(google_directions_cache,f)
            except ValueError:
                print ("cache write failed...")
        time.sleep(1)
    return connection_data

def get_close_ghs(src_hash,lookup_hash_list,gh_precision,max_haversine,min_haversine):
    return [gh for gh in lookup_hash_list
                if gh[0:gh_precision] in src_hash[0:gh_precision]
                and haversine(*reverse_GPS(geohash.decode(src_hash)),*reverse_GPS(geohash.decode(gh))) <= max_haversine
                and haversine(*reverse_GPS(geohash.decode(src_hash)),*reverse_GPS(geohash.decode(gh))) >= min_haversine]
