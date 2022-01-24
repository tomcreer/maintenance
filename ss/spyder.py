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
    
    df_hier = pd.read_pickle('data_pub/df_hier.pickle') 
    return df_vio, df_hier

[df_vio, df_hier] = load_data_init()
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
gdfx['hierarchy'] = st.sidebar.text_input('Hierarchy class', gdf.iloc[selected_chainage[0]].Hier2015)

works_required = st.sidebar.selectbox(
     'Works required',
     ('Overlay', 'Plane & Inlay', 'Midi Paver', 'Microasphalt', 'Surface Dressing', 'HFS', 'Recon - profile', 'Recon - slab stabilisation', 'Reconstruction'))


tm_required = st.sidebar.selectbox(
     'Traffic Management difficulty',
     ('Low', 'Medium', 'High',''))
iron_required = st.sidebar.selectbox(
     'Ironwork difficulty',
     ('Low', 'Medium', 'High',''))

advanced_works_required = st.sidebar.multiselect('Advanced/additional works', ['Patching','Drainage','Kerbing','Footways',''],default='')


gdfx['works_required'] =  works_required
gdfx['tm_required'] = tm_required
gdfx['iron_required'] = iron_required
gdfx['advanced_works_required'] = str(advanced_works_required)

gdfx['notes'] = st.sidebar.text_area('Notes (e.g. existing construction if known)',value='')


gdfx['year'] = st.sidebar.text_input('Planned year', '')
gdfx['priority'] = st.sidebar.selectbox(
     'Priority',
     ('High', 'Medium/High', 'Medium','Medium/Low','Low'))
gdfx['status'] = st.sidebar.selectbox(
     'Scheme status',
     ('Candidate', 'Planned', 'Completed','Deferred'))


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

@st.cache
def gen_shp(fn,gdf_t):
    buffer = BytesIO()
    gdf_t.to_file(filename=fn, driver='ESRI Shapefile')
    shutil.make_archive(fn, 'zip', root_dir = fn)
    shutil.rmtree(fn)
    with open(fn+'.zip', 'rb') as fh:
     buf = BytesIO(fh.read())

    return buf

#fn = 'shp_schemes/'+road_num[0]+'_'+scheme_name+'_'+("%.0f" % area)+'m2'
fn = '/tmp/'+road_num[0]+'_'+scheme_name+'_'+("%.0f" % area)+'m2'
shp_output = gen_shp(fn,gdfx)


st.sidebar.download_button(label='Download Scheme',
                                data=shp_output,
                                file_name=fn[5:]+'.zip',
                                mime="application/zip")
