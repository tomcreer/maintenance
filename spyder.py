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

with open('roadslist.pickle','rb') as f:
    roads = pickle.load(f)
    f.close()
road_num = st.sidebar.multiselect('Road number', roads,default='A1')


@st.cache(allow_output_mutation=True, ttl=3600)
def load_data(road):
    gdf = gpd.read_file('shp_roads/'+road+'.shp')
    gdf.crs = "EPSG:27700"
    def transform_coords(X1,Y1):
        return transformer.transform(X1, Y1)

    
    return gdf

gdf = load_data(road_num[0])
gdf['ch'] = gdf.apply(lambda x: x.name, axis=1)

selected_chainage = st.slider('Section', 0, gdf.shape[0]-1,  \
                              value=(0, gdf.shape[0]-1), step=1)
st.write('Selected area:', selected_chainage)
      
gdfx = gdf.iloc[selected_chainage[0]:selected_chainage[1]+1]#['geometry']


transformer27 = Transformer.from_crs("epsg:27700", "epsg:3857")

x1 = gdfx.bounds.minx.min()
x2 = gdfx.bounds.maxx.max()
y1 = gdfx.bounds.miny.min()
y2 = gdfx.bounds.maxy.max()

new_coords = transformer.transform((x1+x2)/2,(y1+y2)/2)
new_coords1 = transformer.transform(x1,y1)
new_coords2 = transformer.transform(x2,y2)

#new_coords = transformer.transform((coords[0]+coords[2])/2,  (coords[1]+coords[3])/2)
#def transform_coords(X1,Y1):
#    return transformer.transform(X1, Y1)




mapa = folium.Map(location=new_coords, tiles='https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}',attr='google',#'http://{s}.tiles.yourtiles.com/{z}/{x}/{y}.png', #tiles='https://manngis.gov.im/LocalViewWeb/ArcGIS/Rest/Services/6e0ea2cc-77ed-4fdd-aa1f-80be2daa7d7e/MapServer/tile/{z}/{y}/{x}',attr="MANNGIS IoM Gov",
                  zoom_start=17, prefer_canvas=True)




#https://maps.im/geoserver/iom/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&FORMAT=image/png&TRANSPARENT=true&LAYERS=iom:glenvine&TILED=true&WIDTH=256&HEIGHT=256&CRS=EPSG:3857&STYLES=&BBOX=-506318.8753610067,7205871.530500136,-503872.8904558811,7208317.515405262


style1 = {'fillColor': '#b5180d', 'color': '#e30f00'}

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



    
#feature_group4 = folium.FeatureGroup(name='Chainages', show=True)
#def plotChain(point):
#    #iframe = folium.IFrame(text, width=700, height=450)
#    #popup = folium.Popup(iframe, max_width=3000)
#    
#    x2,y2 = transformer27.transform(point.geometry.centroid.x,point.geometry.centroid.y)    
#    folium.Marker( [x2, y2], radius=4
#                     , color='black'
#                     #, fill_color='#808080'
#                     #, fill=True
#                     , icon=folium.DivIcon(html=str("<p style='font-family:verdana;color:#444;font-size:10px;'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s</p>" % (str(point.name))))#, point['LABEL'], point['STARTCH'])))
#                     #, popup=str(point['cumlength'])
#                     ).add_to(feature_group4)#
#
#
#gdf.iloc[selected_chainage[0]:selected_chainage[1]].apply(lambda x: plotChain(x), axis=1)

#tiles test
    
#atlas = folium.raster_layers.WmsTileLayer(url = 'https://maps.im/geoserver/iom/wms?', layers='iom:crosby', name='test', fmt='image/png', attr='test', transparent=True, version='1.3.0')

#atlas.add_to(mapa)


#mapa.add_child(feature_group4)
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
     ('Overlay', 'Plane & Inlay', 'Microasphalt', 'Surface Dressing', 'HFS', 'Recon - profile', 'Recon - slab stabilisation'))


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
     ('Candidate', 'Planned', 'Compete','Deferred'))


cost_matrix_base = {'Overlay':20, 'Plane & Inlay':25, 'Microasphalt':12, 'Surface Dressing':8, 'HFS':30, 'Recon - profile':120, 'Recon - slab stabilisation':150}
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

fn = 'shp_schemes/'+road_num[0]+'_'+scheme_name+'_'+("%.0f" % area)+'m2'
shp_output = gen_shp(fn,gdfx)


st.sidebar.download_button(label='Download Scheme',
                                data=shp_output,
                                file_name=fn,
                                mime="application/zip")
