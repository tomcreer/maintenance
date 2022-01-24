#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 28 13:11:49 2021

@author: tommo
"""


import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
import pickle
from shapely import geometry, ops
import geopandas as gpd

from shapely.geometry import Polygon

from shapely.geometry import LineString
from typing import List

#experimental
def merge_lines(lines: List[LineString]) -> LineString:
    last = None
    points = []
    for line in lines:
        current = line.coords[0]

        if last is None:
            points.extend(line.coords)
        else:
            if last == current:
                points.extend(line.coords[1:])
            else:
                print('Skipping to merge {} {}'.format(last, current))
                return None
        last = line.coords[-1]
    return LineString(points)
        

def cut(line, distance, lines):
    # Cuts a line in several segments at a distance from its starting point
    if distance <= 0.0 or distance >= line.length:
        return [LineString(line)]
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == distance:
            return [
                LineString(coords[:i+1]),
                LineString(coords[i:])
                ]
        if pd > distance:
            cp = line.interpolate(distance)
            lines.append(LineString(coords[:i] + [(cp.x, cp.y)]))
            line = LineString([(cp.x, cp.y)] + coords[i:])
            if line.length > distance:
                cut(line, distance, lines)
            else:
                lines.append(LineString([(cp.x, cp.y)] + coords[i:]))
            return lines

#Load in the roads hierarchy polylines
gdf_hier = gpd.read_file('data/Road Hierarchy.shp')
gdf_hier.head()
gdf_hier.crs = 'epsg:27700'
    
#load in the roads list
with open('roadslist.pickle','rb') as f:
    loaded_list = pickle.load(f)
    f.close()
    
#load in the Manxmap polygons
gdf  = gpd.read_file('data/RoadShape.shp')

#filter Manxmap to just roads & junctions
#9014003 = roads
#9014008 = junctions
#9014007 = footways
gdf2 = gdf[(gdf.FEATURE_CO == '9014003') | (gdf.FEATURE_CO == '9014008')]
gdf_f = gdf[gdf.FEATURE_CO == '9014007']

#join all hierarchy lines with same road number
gdf_hier2 = gdf_hier.dissolve(by='ROAD_NUM', aggfunc='sum')
gdf_hier2.reset_index(level=0, inplace=True)

#set column to string 
gdf_hier2['ROAD_NUM'] = gdf_hier2['ROAD_NUM'].astype(str)
gdf_hier2.head(100)

#get columns back
gdf_hier['ROAD_NUM'] = gdf_hier['ROAD_NUM'].astype(str)
gdf_hier3 = gdf_hier2.merge(gdf_hier[['ROAD_NUM','PROP_NAME','CLASS','Hier2015']], on='ROAD_NUM', how='left')
gdf_hier3 = gdf_hier3.drop_duplicates(subset='ROAD_NUM', keep="first")

#loop through for each road
for y,roadnum in enumerate(loaded_list):
#for y in range(0,1):
    #roadnum = 'A3'
    #where programme crashes
    #if y < 788:
    #    continue
    
    #deal with edge cases
    if roadnum is None:
     continue
    if gdf_hier3[gdf_hier3['ROAD_NUM']==roadnum].shape[0]:
     #get index of specified road name
     idx = gdf_hier3[gdf_hier3['ROAD_NUM']==roadnum].iloc[0].name
    else:
     print(roadnum + ' no geom')
     continue
    
    #keep just the Manxmap polygons that touch our road polyline
    gdf3 = gpd.sjoin(gdf2, gdf_hier3.loc[[idx]], how='inner', op='intersects')
    if gdf3.shape[0] == 0:
     print(roadnum + ' no geom')
     continue       


    if 1:
        #This sorts the lines so they are in order (have to explode and reassemble)
        df = gpd.GeoDataFrame(geometry=gdf_hier3.loc[[idx]].geometry.explode())
        multitline = geometry.MultiLineString(df.geometry.tolist())
        merged = ops.linemerge(multitline)
        
        startstop = []
        for line in multitline:
            coords = [c for c in line.coords]
            startstop.append((coords[0],coords[:-1]))
        
        collection = ops.split(merged, geometry.MultiPoint(startstop))
        A1 = gpd.GeoDataFrame(geometry=[line for line in collection])

    
    #Split our road line into 10m segments
    lines = []
    for line in (A1.geometry.explode()):
        lines.append(cut(line, 10, list()))
        
    lines = [item for sublist in lines for item in sublist]
    
    # Buffer the 10m segments either side
    polys = []
    for x,l in enumerate(lines):
        polys.append(l.buffer(10.0, single_sided=True) | l.buffer(-10.0, single_sided=True))

    #put back into a GeoDataFrame
    gdfx = gpd.GeoDataFrame(index=range(0,len(polys)))#, crs='epsg:27700', geometry=[polys])
    gdfx['geometry'] = polys
    gdfx.crs = 'epsg:27700'
    
    # Cut these buffered segments against original Manxmap polygon area
    ###gdf_A1_segments = gpd.overlay( gdfx,gdf3, how='intersection')
    gdf_A1_segments = gpd.overlay( gdfx,gdf_f, how='intersection')
    
    #Export to shp
    ###gdf_A1_segments.to_file('shp_roads/'+str(roadnum)+'.shp')
    if gdf_A1_segments.shape[0]:
      gdf_A1_segments.to_file('shp_footways/'+str(roadnum)+'.shp')
    
    print('%s   %i' % (roadnum, y))