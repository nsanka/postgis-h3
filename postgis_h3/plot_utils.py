import h3
import json
import folium
from IPython.display import display
from shapely import from_wkt, to_geojson

def visualize_hexagons(hexagons, color="red", folium_map=None):
   """
   Visualize hexagons on a folium map.
   Args:
      hexagons : list of hexclusters, each hexcluster is a list of hexagons
      color : color of the hexagons
      folium_map : folium map object
   Returns:
      folium map object with hexagons drawn on it.
   """
   polylines = []
   lat = []
   lng = []
   for hex in hexagons:
      polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
      # flatten polygons into loops.
      outlines = [loop for polygon in polygons for loop in polygon]
      polyline = [outline + [outline[0]] for outline in outlines][0]
      lat.extend(map(lambda v:v[0],polyline))
      lng.extend(map(lambda v:v[1],polyline))
      polylines.append(polyline)

   if folium_map is None:
      m = folium.Map(location=[sum(lat)/len(lat), sum(lng)/len(lng)], zoom_start=13, tiles='cartodbpositron')
   else:
      m = folium_map
   for polyline in polylines:
      my_PolyLine=folium.PolyLine(locations=polyline,weight=8,color=color)
      m.add_child(my_PolyLine)
   return m

def visualize_polygon(polyline, color, folium_map=None):
   """
   Visualize a polygon on a folium map.
   Args:
      polyline : list of lat, lng pairs
      color : color of the polygon
   Returns:
      folium map object with polygon drawn on it.
   """
   lat, lng = list(zip(*polyline))
   if folium_map is None:
      m = folium.Map(location=[sum(lat)/len(lat), sum(lng)/len(lng)], zoom_start=13, tiles='cartodbpositron')
   else:
      m = folium_map
   my_PolyLine=folium.PolyLine(locations=polyline,weight=8,color=color)
   m.add_child(my_PolyLine)
   return m

def visualize_hex_polygon(data, row):
   """
   Visualize hexagons and polygon on a folium map.
   Args:
      data : dataframe containing geometry
      row : row index of the data
   Returns:
      folium map object with hexagons and polygon drawn on it.
   """
   geoJson = json.loads(to_geojson(from_wkt(data.loc[row, 'geometry'])))
   if data.loc[row, 'geom_type'] == 'POLYGON':
      polyline = [[p[1], p[0]] for p in geoJson['coordinates'][0]]
   elif data.loc[row, 'geom_type'] == 'MULTIPOLYGON':
      polyline = [[p[1], p[0]] for coord in geoJson['coordinates'] for row in coord for p in row]
   elif data.loc[row, 'geom_type'] == 'LINESTRING':
      polyline = [[p[1], p[0]] for p in geoJson['coordinates']]
   elif data.loc[row, 'geom_type'] == 'POINT':
      polyline = [[geoJson['coordinates'][1], geoJson['coordinates'][0]]]
      polyline.append(polyline[0])
   m = visualize_polygon(polyline, color="green")
   m = visualize_hexagons(data.loc[row, 'h3_index'], 'red', folium_map=m)
   return m


def main():
   # lat, lng, hex resolution
   h3_address = h3.geo_to_h3(37.3615593, -122.0553238, 9)
   m = visualize_hexagons([h3_address])
   display(m)

   hex_center_coordinates = h3.h3_to_geo(h3_address) # array of [lat, lng]
   hex_boundary = h3.h3_to_geo_boundary(h3_address) # array of arrays of [lat, lng lng]
   m = visualize_hexagons(list(h3.k_ring_distances(h3_address, 4)[3]), color="purple")
   m = visualize_hexagons(list(h3.k_ring_distances(h3_address, 4)[2]), color="blue", folium_map=m)
   m = visualize_hexagons(list(h3.k_ring_distances(h3_address, 4)[1]), color="green", folium_map=m)
   m = visualize_hexagons(list(h3.k_ring_distances(h3_address, 4)[0]), color = "red", folium_map=m)
   display(m)

if __name__ == "__main__":
   main()