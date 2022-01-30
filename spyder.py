    # -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from io import BytesIO
import streamlit as st
from streamlit_folium import folium_static
import folium, pickle, shutil, base64
import geopandas as gpd
import pandas as pd
import numpy as np
#import altair as alt
import datetime

from streamlit_folium import folium_static
import folium
from pyproj import Transformer
transformer = Transformer.from_crs("epsg:27700", "epsg:4326")

st.markdown(
    f'''
        <style>
            .sidebar .sidebar-content {{
                width: 800px;
            }}
        </style>
    ''',
    unsafe_allow_html=True
)

st.write(
     """
#     Roads maintenance mapper
#     """
)
#with st.echo():

@st.cache(allow_output_mutation=True, ttl=3600)
def load_data_init():
    df_vio = pd.read_pickle('data_pub/df_vio.pickle') 
    df_vio['roadcode'], df_vio['roadsection'] = df_vio['SECTION_RF'].str.split('_',1).str
    df_vio['X1'] = df_vio['Latitude']
    df_vio['Y1'] = df_vio['Longitude']
    df_vio['Pavement condition'] = pd.to_numeric(df_vio['Pavement condition'])
    gdf_gaz = gpd.read_file('data_pub/gazetteer.shp')

    
    df_hier = pd.read_pickle('data_pub/df_hier.pickle') 
    return df_vio, df_hier, gdf_gaz

[df_vio, df_hier, gdf_gaz] = load_data_init()
roadname = st.sidebar.selectbox(
     'Road name?',
     (np.insert(df_hier.PROP_NAME.unique(),0,'')))

with open('roadslist.pickle','rb')  as f:
    roads = pickle.load(f)
    f.close()

if roadname != '':
  default = df_hier[df_hier['PROP_NAME']==roadname].ROAD_NUM.mode()[0]
  road_num = st.sidebar.multiselect('Road number', roads,default=default)
else:
  road_num = st.sidebar.multiselect('Road number', roads,default='A1')


@st.cache(allow_output_mutation=True, ttl=3600)
def load_data(road):
    gdf = gpd.read_file('shp_roads/'+road+'.shp')
    gdf.crs = "EPSG:27700"
    def transform_coords(X1,Y1):
        return transformer.transform(X1, Y1)


    df_CL1 = pd.read_pickle('data_pub/CL1.pickle')
    df_CR1 = pd.read_pickle('data_pub/CR1.pickle') 
    
    #pd.read_xls('video_export__isle_of_man__2021_11_30__20_19__utc.xlsx')
    #df_vio = pd.read_pickle('data_pub/df_vio.pickle') 
    #df_vio['roadcode'], df_vio['roadsection'] = df_vio['SECTION_RF'].str.split('_',1).str
    #df_vio['X1'] = df_vio['Latitude']
    #df_vio['Y1'] = df_vio['Longitude']
    #df_vio['Pavement condition'] = pd.to_numeric(df_vio['Pavement condition'])
    return gdf, df_CL1, df_CR1#, df_vio

[gdf, df_CL1, df_CR1] = load_data(road_num[0])
gdf['ch'] = gdf.apply(lambda x: x.name, axis=1)

selected_chainage = st.slider('Section', 0, gdf.shape[0]-1,  \
                              value=(0, gdf.shape[0]-1), step=1)
st.write('Selected area:', selected_chainage)

startch = selected_chainage[0]
endch = selected_chainage[1]

gdfx = gdf.iloc[startch:endch]#['geometry']
transformer27 = Transformer.from_crs("epsg:27700", "epsg:3857")

x1 = gdfx.bounds.minx.min()
x2 = gdfx.bounds.maxx.max()
y1 = gdfx.bounds.miny.min()
y2 = gdfx.bounds.maxy.max()

new_coords = transformer.transform((x1+x2)/2,(y1+y2)/2)
new_coords1 = transformer.transform(x1,y1)
new_coords2 = transformer.transform(x2,y2)

mapa = folium.Map(location=new_coords, tiles='https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}',attr='google',#'http://{s}.tiles.yourtiles.com/{z}/{x}/{y}.png', #tiles='https://manngis.gov.im/LocalViewWeb/ArcGIS/Rest/Services/6e0ea2cc-77ed-4fdd-aa1f-80be2daa7d7e/MapServer/tile/{z}/{y}/{x}',attr="MANNGIS IoM Gov",
                  zoom_start=17, prefer_canvas=True)




#https://maps.im/geoserver/iom/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&FORMAT=image/png&TRANSPARENT=true&LAYERS=iom:glenvine&TILED=true&WIDTH=256&HEIGHT=256&CRS=EPSG:3857&STYLES=&BBOX=-506318.8753610067,7205871.530500136,-503872.8904558811,7208317.515405262


style1 = {'fillColor': '#d1d1d1', 'color': '#404040'}

folium.GeoJson(data=gdfx,#.iloc[:1000],
    style_function=lambda x:style1,
    tooltip=folium.features.GeoJsonTooltip(
        fields=['ch'],
        aliases=['ch'], 
        labels=True, 
        sticky=True,
        toLocaleString=True
    )
              
              
              ).add_to(mapa)


feature_group6 = folium.FeatureGroup(name='RCIexTex', show=False)
feature_group7 = folium.FeatureGroup(name='LSUR', show=False)
feature_group8 = folium.FeatureGroup(name='Vaisala', show=False)

from branca.colormap import LinearColormap

color_scale = {}

df_CL1_road = df_CL1[df_CL1['roadcode']==road_num[0]]
df_CR1_road = df_CR1[df_CR1['roadcode']==road_num[0]]
df_vio_road = df_vio[df_vio['roadcode']==road_num[0]]

lim1 = df_CL1_road[['smoothedmap']].rolling(1).mean().fillna(0).describe().iloc[4,0]
lim2 = df_CL1_road[['smoothedmap']].rolling(1).mean().fillna(0).describe().iloc[[2,1],0].sum()*5/3
lim3 = df_CL1_road[['smoothedmap2']].rolling(1).mean().fillna(0).describe().iloc[4,0]
lim4 = df_CL1_road[['smoothedmap2']].rolling(1).mean().fillna(0).describe().iloc[[2,1],0].sum()*5/3

diff = lim2-lim1
diff2 = lim4-lim3

if True in np.isnan([lim1,lim2,diff]):
    lim1 = 0
    lim2 = 200
    diff = 50
if True in np.isnan([lim3,lim4,diff2]):
    lim3 = 0
    lim4 = 0.8
    diff2 = 0.2

color_scale = LinearColormap(['#91db9b','yellow','red'], index=[lim1,lim2-diff/2,lim2-diff/6])       
color_scale2 = LinearColormap(['#91db9b','yellow','red'], index=[lim3,lim4-diff2/2,lim4-diff2/6])       

color_scalevio = LinearColormap(['red','#ff5736','yellow','#91db9b',], index=[40,89,96,100])       

def plotDot(point,feature_group,to_plot='smoothedmap',color_scale=color_scale):
    size = 2
    
    #x2,y2 = transformer27.transform(point['X1'],point['Y1'])    
    x2,y2 = point['X1'],point['Y1']
    
    folium.Circle( [x2, y2], radius=size
                     , color=color_scale(float(point[to_plot])) #'RCIexTex'
                     #, fill_color='black'
                     , fill=True
                     ).add_to(feature_group)

if df_CL1_road.shape[0] > 1000:
    spacing = 3
if df_CL1_road.shape[0] > 500:
    spacing = 2
else:
    spacing = 1


if df_CL1_road.shape[0]:
    df_CL1_road.iloc[1::spacing].apply(lambda x: plotDot(x,feature_group6,'smoothedmap',color_scale), axis = 1)  
    df_CL1_road.iloc[1::spacing].apply(lambda x: plotDot(x,feature_group7,'smoothedmap2',color_scale2), axis = 1)  
if df_CR1_road.shape[0]:
    df_CR1_road.iloc[1::spacing].apply(lambda x: plotDot(x,feature_group6,'smoothedmap',color_scale), axis = 1)  
    df_CR1_road.iloc[1::spacing].apply(lambda x: plotDot(x,feature_group7,'smoothedmap2',color_scale2), axis = 1)  
if df_vio_road.shape[0]:
    df_vio_road.iloc[1::spacing].apply(lambda x: plotDot(x,feature_group8,'Pavement condition',color_scalevio), axis = 1)  

mapa.add_child(feature_group6)
mapa.add_child(feature_group7)
mapa.add_child(feature_group8)


folium.TileLayer('openstreetmap').add_to(mapa)
mapa.add_child(folium.map.LayerControl())

mapa.fit_bounds([new_coords1, new_coords2]) 


folium_static(mapa)



st.write('Selected area:',  "%.0f" % gdfx.geometry.area.sum() + " m2")

gdfx = gdfx.dissolve(by='ROAD_NUM')
area =  gdfx.geometry.area.sum()

gdfx['area'] = area
scheme_name = st.sidebar.text_input('Scheme Name', '')
gdfx['scheme_name'] = scheme_name
hierarchy = st.sidebar.text_input('Hierarchy class', gdf.iloc[selected_chainage[0]].Hier2015)
hierarchy_domain = {'Access':'A','District':'D','Footpath':'FP','Information':'I',
                    'Local':'L','Primary':'P','Private':'PRV','Public Right of Way':'PROW','Unsurfaced':'UNS'}


gdfx['hierarchy'] = hierarchy_domain[hierarchy]

works_required = st.sidebar.selectbox(
     'Works required',
     ('Overlay', 'Plane & Inlay', 'Midi Paver', 'Microasphalt', 'Surface Dressing', 'HFS', 'Recon - profile', 'Recon - slab stabilisation', 'Reconstruction'))

works_required_domain = {'Overlay':'OVR',
'Plane & Inlay':'P&I',
'Midi Paver':'MID',
'Microasphalt':'MIC',
'Surface Dressing':'SUR',
'HFS':'HFS',
'Recon - profile':'REP',
'Recon - slab stabilisation':'RES',
'Reconstruction':'REC'}

highmediumlow_domain = {'High':'H','Medium':'M','Low':'L'}
priority_domain = {'High':9,'Medium/High':7,'Medium':5,'Medium/Low':3,'Low':1}
yesno_domain = {'Yes':'Y','No':'N'}

tm_required = st.sidebar.selectbox(
     'Traffic Management difficulty',
     ('Low', 'Medium', 'High',''))
iron_required = st.sidebar.selectbox(
     'Ironwork difficulty',
     ('Low', 'Medium', 'High',''))

adv_work_domain = ['Patching','Drainage','Kerbing','Footways','']
advanced_works_required = st.sidebar.multiselect('Advanced/additional works', adv_work_domain,default='')
for adv_work in adv_work_domain:
    if adv_work != '':
     if adv_work in advanced_works_required:
        gdfx[adv_work] = 'Y'
     else:
        gdfx[adv_work] = 'N'

gdfx['works_required'] =  works_required_domain[works_required]

gdfx['tm_required'] = highmediumlow_domain[tm_required]
gdfx['iron_required'] = highmediumlow_domain[iron_required]
gdfx['advanced_works_required'] = str(advanced_works_required)

gdfx['notes'] = st.sidebar.text_area('Notes (e.g. existing construction if known)',value='')


gdfx['year'] =  st.sidebar.date_input("Planned date",datetime.date(2022, 4, 1))

priority = st.sidebar.selectbox(
     'Priority',
     ('High', 'Medium/High', 'Medium','Medium/Low','Low'))

gdfx['priority'] = priority_domain[priority]

status = st.sidebar.selectbox(
     'Scheme status',
     ('Candidate', 'Planned', 'Completed','Deferred'))

status_domain = {'Candidate':'CND', 'Planned':'PLN', 'Completed':'CMP','Deferred':'DEF'}
gdfx['status'] = status_domain[status]


cost_matrix_base = {'Overlay':20, 'Plane & Inlay':25, 'Microasphalt':12, 'Midi Paver':17, 'Surface Dressing':8, 'HFS':30, 'Recon - profile':120, 'Recon - slab stabilisation':150,'Reconstruction':120}
cost_matrix_tm = {'Low':1.0, 'Medium':1.2, 'High':1.4,'':1.0}
cost_matrix_iron = {'Low':1.0, 'Medium':1.1, 'High':1.2,'':1.0}
cost_matrix_add = {'Patching':1.1,'Drainage':1.2,'Kerbing':1.1,'Footways':1.2,'':1.0}

est_cost_pre = area * cost_matrix_base[works_required] * cost_matrix_tm[tm_required] * cost_matrix_iron[iron_required]
#if len(cost_matrix_add):
for costs in advanced_works_required:
    est_cost_pre = est_cost_pre * cost_matrix_add[costs]
est_cost_pre -= est_cost_pre % -100
gdfx['est_cost'] = st.sidebar.number_input('Estimated Cost (£)', round(est_cost_pre), format="%i")

gdfx.crs = 'epsg:27700'

##match USRN
gdf_gaz2 = gdf_gaz[gdf_gaz['RoadNum'] == road_num[0]]
gdfx['Type3USRN'] = int(gpd.sjoin(gdf_gaz2, gdfx, op='intersects')['Type3USRN'].mode()[0])


gdfx['SchemeRef'] = '22/000x'
gdfx['DashboardC'] = 1
gdfx['RoadNo'] = road_num

column_match = {'area':'SHAPE_STAr',
        'LENGTH':'SHAPE_STLe',
        'PROP_NAME':'StreetName',
       'scheme_name':'SchemeName',
       'hierarchy':'RoadHierar',
       'works_required':'WorksReq',
       'tm_required':'TMDiff',
       'iron_required':'IronworkDi',
       'notes':'Notes',
       'year':'SchemeDate',
       'priority':'Priority', 
       'status':'Status',
       'est_cost':'EstCost',
       'Type3USRN':'USRN'
                }

gdfx.rename(columns=column_match, inplace=True)

del gdfx['TOID']
del gdfx['VERSIONDAT']
del gdfx['CALCULATED']
del gdfx['index_righ']
del gdfx['CLASS']
del gdfx['Hier2015']
del gdfx['ch']
del gdfx['advanced_works_required']
#del gdfx['ROAD_NUM']

import os, fiona
from slugify import slugify

from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon



@st.cache
def gen_shp(fn,gdf_t,schema):
    buffer = BytesIO()
    gdf_t["geometry"] = [MultiPolygon([feature]) if type(feature) == Polygon \
    else feature for feature in gdf_t["geometry"]]
    gdf_t.to_file(filename=fn, driver='ESRI Shapefile', schema=schema)
    #gdf_t.to_file(fn+'.gpkg', layer=slugify(scheme_name), driver="GPKG")
    shutil.make_archive(fn, 'zip', root_dir = fn)
    shutil.rmtree(fn)
    with open(fn+'.zip', 'rb') as fh:
     buf = BytesIO(fh.read())

    return buf

#gdfx['SchemeDate'] = pd.to_datetime(gdf['SchemeDate'], format='%Y')

# schema = {'geometry': 'MultiPolygon', 
#           'properties': {'FEATURE_CO': 'str', 
#                                      'SHAPE_STLe': 'float',
#                                      'StreetName': 'str',
#                                      'SHAPE_STAr': 'float',
#                                      'SchemeName': 'str',
#                                      'RoadHierar': 'str',
#                                      'Patching': 'str',
#                                      'Drainage': 'str',
#                                      'Kerbing': 'str',
#                                      'Footways': 'str',
#                                      'WorksReq': 'str',
#                                      'TMDiff': 'str',
#                                      'IronworkDi': 'str',
#                                      'Notes': 'str',
#                                      'SchemeDate': 'date',
#                                      'Priority': 'int',
#                                      'Status': 'str',
#                                      'EstCost': 'int',
#                                      'Type3USRN': 'int',
#                                      'SchemeRef': 'str',
#                                      'DashboardC': 'int'}}

from collections import OrderedDict
schema = {'geometry': 'MultiPolygon', 'properties': OrderedDict([('FEATURE_CO', 'str'),
                                                                 ('ROAD_NUM', 'str'), 
                                                                 ('SHAPE_STLe', 'float'), 
                                                                 ('StreetName', 'str'), 
                                                                 ('SHAPE_STAr', 'float'), 
                                                                 ('SchemeName', 'str'), 
                                                                 ('RoadHierar', 'str'), 
                                                                 ('Patching', 'str'), 
                                                                 ('Drainage', 'str'), 
                                                                 ('Kerbing', 'str'), 
                                                                 ('Footways', 'str'), 
                                                                 ('WorksReq', 'str'), 
                                                                 ('TMDiff', 'str'), 
                                                                 ('IronworkDi', 'str'), 
                                                                 ('Notes', 'str'), 
                                                                 ('SchemeDate', 'date'), 
                                                                 ('Priority', 'int32:4'), 
                                                                 ('Status', 'str'), 
                                                                 ('EstCost', 'float'), 
                                                                 ('USRN', 'str'), 
                                                                 ('SchemeRef', 'str'), 
                                                                 ('RoadNo','str'),
                                                                 ('DashboardC', 'int32:4')])}

#fn = 'shp_schemes/'+road_num[0]+'_'+scheme_name+'_'+("%.0f" % area)+'m2'
fn = '/tmp/'+road_num[0]+'_'+scheme_name+'_'+("%.0f" % area)+'m2'
shp_output = gen_shp(fn,gdfx, schema)


st.sidebar.download_button(label='Download Scheme',
                                data=shp_output,
                                file_name=fn[5:]+'.zip',#'gkpg',
                                mime="application/zip")#"geopackage+sqlite3")
