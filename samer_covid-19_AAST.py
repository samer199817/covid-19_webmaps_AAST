"""
This program is designed to take covid-19 data and a shapefile
from the internet and wrangle the data then produce webmaps in html
"""

# resources
# the covid-19 data provided by johns-hopkins-university 
# https://github.com/CSSEGISandData/COVID-19.git  


import os
import wget
import datetime
import time
import folium
from folium import plugins
import branca.colormap as cm
import geopandas as gpd
import numpy as np
import pandas as pd
import altair as alt

# so that u don't have warnings
from warnings import filterwarnings

filterwarnings('ignore')


c = 0
start_time = time.time()
# an introduction
print('Hello \n'
      'This program is designed to take covid-19 data and a shapefile \n'
      'from the internet and wrangle the data then produce webmaps in html. \n')


# path creation
current_path = os.getcwd()
data_path = current_path + '\\data_down'
webmaps_path = current_path + '\\webmaps'
shapefile_path = current_path + '\\shapefile'
csv_path = current_path + '\\csv and shapefiles'

# creating a folder to host the downloaded data
if not os.path.exists(data_path):
    os.mkdir(data_path)

# creating a folder to host the webmaps
if not os.path.exists(webmaps_path):
    os.mkdir(webmaps_path)

# creating a folder to host the csv files
if not os.path.exists(csv_path):
    os.mkdir(csv_path)


# getting required files from the internet
urls = [
    'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'
    'time_series_covid19_confirmed_global.csv',
    'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'
    'time_series_covid19_deaths_global.csv',
    'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'
    'time_series_covid19_recovered_global.csv']


# deleting old csv files
if os.path.isfile(data_path + '\\time_series_covid19_confirmed_global.csv'):
    os.unlink(data_path + '\\time_series_covid19_confirmed_global.csv')
if os.path.isfile(data_path + '\\time_series_covid19_deaths_global.csv'):
    os.unlink(data_path + '\\time_series_covid19_deaths_global.csv')
if os.path.isfile(data_path + '\\time_series_covid19_recovered_global.csv'):
    os.unlink(data_path + '\\time_series_covid19_recovered_global.csv')

# downloading the required files
for url in urls:
    filename = wget.download(url, out=data_path)
print('The needed files was downloaded.')
# inserting the required files
df_confirmed = pd.read_csv(data_path + '\\time_series_covid19_confirmed_global.csv')
df_death = pd.read_csv(data_path + '\\time_series_covid19_deaths_global.csv')
df_recovered = pd.read_csv(data_path + '\\time_series_covid19_recovered_global.csv')
world = gpd.read_file(shapefile_path + '\\World_Map.shp')
print('The program read the needed files.')

# getting the dates
dates = df_confirmed.columns[4:]

# melt dataframes into pivot like dataframes
df_confirmed_melt = df_confirmed.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
                                      value_vars=dates, var_name='Date', value_name='Confirmed')

df_death_melt = df_death.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
                              value_vars=dates, var_name='Date', value_name='Deaths')

df_recovered_melt = df_recovered.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
                                      value_vars=dates, var_name='Date', value_name='Recovered')

# merging dataframes to get all values together
df = pd.merge(left=df_confirmed_melt, right=df_death_melt, how='left',
              on=['Province/State', 'Country/Region', 'Date', 'Lat', 'Long'])

df = pd.merge(left=df, right=df_recovered_melt, how='left',
              on=['Province/State', 'Country/Region', 'Date', 'Lat', 'Long'])

# Convert to datetime format
df['Date'] = pd.to_datetime(df['Date'])

# fill null with 0
df['Recovered'] = df['Recovered'].fillna(0)

# converting the Recovered column into int datatype
df['Recovered'] = df['Recovered'].astype('int')

# removing extra recovered values from the merge
df = df[df['Province/State'].str.contains('Recovered') != True]

# removing county wise data to avoid double values
df = df[df['Province/State'].str.contains(',') != True]

# creating an Active column for analysis 
df['Active'] = df['Confirmed'] - df['Deaths'] - df['Recovered']

cols = ['Confirmed', 'Deaths', 'Recovered', 'Active']
# giving all the null values (0)
df[cols] = df[cols].fillna(0)

# Grouping by day, country for improving the quality of the data
full_grouped = df.groupby(['Date', 'Country/Region'])['Confirmed', 'Deaths', 'Recovered', 'Active'].sum().reset_index()

# creating the new cases columns
temp = full_grouped.groupby(['Country/Region', 'Date', ])['Confirmed', 'Deaths', 'Recovered']
temp = temp.sum().diff().reset_index()

mask = temp['Country/Region'] != temp['Country/Region'].shift(1)

temp.loc[mask, 'Confirmed'] = np.nan
temp.loc[mask, 'Deaths'] = np.nan
temp.loc[mask, 'Recovered'] = np.nan

# renaming columns 
temp.columns = ['Country/Region', 'Date', 'New cases', 'New deaths', 'New recovered']

# merging new values
full_grouped = pd.merge(full_grouped, temp, on=['Country/Region', 'Date'])

# filling na with 0
full_grouped = full_grouped.fillna(0)

# fixing data types
cols = ['New cases', 'New deaths', 'New recovered']
full_grouped[cols] = full_grouped[cols].astype('int')

full_grouped['New cases'] = full_grouped['New cases'].apply(lambda x: 0 if x < 0 else x)

full_grouped = full_grouped.groupby(['Date', 'Country/Region'])[
    'Confirmed', 'Deaths', 'Recovered', 'New cases', 'New deaths', 'New recovered'].sum().reset_index()

# renaming columns
full_grouped.rename(columns={'Country/Region': 'Country'}, inplace=True)

full_grouped = full_grouped[full_grouped.Country != 'Diamond Princess']
full_grouped = full_grouped[full_grouped.Country != 'MS Zaandam']
full_grouped = full_grouped[full_grouped.Country != 'Summer Olympics 2020']

# dropping two null values in china and in canada and renaming DataFrame
df = full_grouped.dropna()

# dropping islands that can affect the data
df = df[df.Country != 'Diamond Princess']
df = df[df.Country != 'MS Zaandam']
df = df[df.Country != 'Summer Olympics 2020']
# this two are extra from another column but i left them just for remembering if i wanted to use them again
# df = df[df.State!='Grand Princess'] 
# df = df[df.State!='Diamond Princess']

# This places doesn't have population data 
# Åland Islands, Bouvet Island, British Indian Ocean Territory, Cocos (Keeling) Islands, French Southern and Antarctic Lands, 
# Guernsey, Heard Island and McDonald Islands, Jersey islands, Netherlands Antilles, Norfolk Island, Green land
# Pitcairn Islands, Saint Helena, Svalbard, United States Minor Outlying Islands, Wallis and Futuna Islands

# the shapefile data didn't match the DataFrame
# editing the Country names to match the DataFrame
world.replace('Viet Nam', 'Vietnam', inplace=True)
world.replace('Brunei Darussalam', 'Brunei', inplace=True)
world.replace('Cape Verde', 'Cabo Verde', inplace=True)
world.replace('Democratic Republic of the Congo', 'Congo (Kinshasa)', inplace=True)
world.replace('Congo', 'Congo (Brazzaville)', inplace=True)
world.replace('Czech Republic', 'Czechia', inplace=True)
world.replace('Swaziland', 'Eswatini', inplace=True)
world.replace('Iran (Islamic Republic of)', 'Iran', inplace=True)
world.replace('Korea, Republic of', 'Korea, South', inplace=True)
world.replace("Lao People's Democratic Republic", 'Laos', inplace=True)
world.replace('Libyan Arab Jamahiriya', 'Libya', inplace=True)
world.replace('Republic of Moldova', 'Moldova', inplace=True)
world.replace('The former Yugoslav Republic of Macedonia', 'North Macedonia', inplace=True)
world.replace('Syrian Arab Republic', 'Syria', inplace=True)
world.replace('Taiwan', 'Taiwan*', inplace=True)
world.replace('United Republic of Tanzania', 'Tanzania', inplace=True)
world.replace('United States', 'US', inplace=True)
world.replace('Palestine', 'West Bank and Gaza', inplace=True)

# editing the Dataframe names to match the open street map
df.replace('South Sudan', 'Sudan', inplace=True)
df.replace('Micronesia', 'Federated States of Micronesia', inplace=True)
df.replace('Taiwan*', 'Taiwan', inplace=True)

# matching the column's name for a better match
world.rename(columns={'NAME': 'Country'}, inplace=True)

# Merging the 'data' with 'world' geopandas geodataframe
# gdf = world.merge(df, on=['Country'])

# grouping the places together because it was created based on regions
df = full_grouped.groupby(['Date', 'Country'])['Confirmed', 'Deaths', 'Recovered', 'New cases',
                                               'New deaths'].sum().reset_index()

# if the latitude and longitude file is not in ur drive the program will create one using osm
if not os.path.isfile(shapefile_path + r'\\countries.csv'):
    map_time = time.time()
    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent="app")
    lat = []
    lon = []
    df_country = df[df['Date'] == str(df['Date'].tolist())[-22:-12]][['Country', 'Confirmed']]
    co_lis = df_country.Country.unique()
    for location in co_lis:
        location = geolocator.geocode(location)
        if location is None:
            lat.append(np.nan)
            lon.append(np.nan)
        else:
            lat.append(location.latitude)
            lon.append(location.longitude)
    df_country['Lat'] = lat
    df_country['Long'] = lon
    df_country = df_country[['Country', 'Lat', 'Long']]
    df_country.to_csv(shapefile_path + r'\\countries.csv')

    end_time = time.time()
    total_time = end_time - map_time
    total_time = time.strftime("%M:%S", time.gmtime(total_time))
    print('The program created a file for latitude and longitude from OSM and '
          'saved it as a csv file in', total_time + '.')

# turing values to positive in the New cases and New deaths
df['New deaths'] = abs(df['New deaths'])
df['New cases'] = abs(df['New cases'])

# opening the latitude and longitude file for merging it with the Dataframe
df_country = pd.read_csv(shapefile_path + r'\\countries.csv')
df_country = df_country[['Country', 'Lat', 'Long']]
print('The program read the latitude and longitude file.')

# removing non useful data
df = df[df['Confirmed'] != 0]

# merging dataframes for adding latitude and longitude
df = pd.merge(left=df, right=df_country, how='left', on=['Country'])
df.to_csv(csv_path + r'\\df.csv')
# creating a total dataframe for the analysis
total = df[df['Date'] == str(df['Date'].tolist())[-22:-12]][
    ['Country', 'Confirmed', 'Deaths', 'Lat', 'Long']]
total = total[['Country', 'Confirmed', 'Deaths', 'Lat', 'Long']].reset_index()
total = total[['Country', 'Confirmed', 'Deaths', 'Lat', 'Long']]
# saving the total dataframe as a csv file
total.to_csv(csv_path + r'\\total.csv')
print('The program saved the total cases and deaths as a csv file.')
# creating a shape file contains the total cases and deaths
gdf = world.merge(total, on=['Country'])
gdf.to_file(csv_path + r'\\total.shp')
print('The program saved the total cases and deaths as a shapefile.')

# creating a total dataframe for the analysis
daily = df[['Country', 'New cases', 'New deaths', 'Lat', 'Long']]
print('The program saved the daily cases and deaths as a csv file.')

# saving the daily dataframe as a csv file
daily.to_csv(csv_path + r'\\daily.csv')

# creating a temporary Dataframe that starts after 01-04-2020 for the line chart
df_temp = df[df['Date'] >= '2020-04-01']

# plot basemaps
World_Imagery_tile = folium.raster_layers.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/'
                                                          'World_Imagery/MapServer/tile/{z}/{y}/{x}',
                                                    attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                                                    name='ESRI World Imagery',
                                                    show=False)

ocean_tile = folium.raster_layers.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/'
                                                  'Ocean_Basemap/MapServer/tile/{z}/{y}/{x}',
                                            attr='Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri',
                                            name='ESRI ocean tile',
                                            show=True)

grey_canvas_tile = folium.raster_layers.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/'
                                                        'World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
                                                  attr='Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
                                                  name='ESRI grey canvas',
                                                  show=False)

Dark_bm = folium.raster_layers.TileLayer(tiles='CartoDB Dark_Matter',
                                         name='Dark basemap',
                                         show=False)

# creating maps with a time slider
map_time = time.time()

gdf = df.merge(world, on='Country')

# creating a date column in epoch format and turning it to a string
gdf['date'] = (gdf['Date'] - datetime.datetime(1970, 1, 1)).dt.total_seconds()
gdf['date'] = gdf['date'].astype(int).astype(str)

# removing extra columns
gdf = gdf[['Country', 'date', 'New cases', 'New deaths', 'geometry']]

# resting index
gdf = gdf.sort_values(['Country', 'date']).reset_index(drop=True)

# creating a color map for the New cases
max_colour = gdf['New cases'].quantile(0.9)
min_colour = 0
cmap = cm.linear.YlGn_09.scale(min_colour, max_colour)
gdf['colour'] = gdf['New cases'].map(cmap)

# creating a style dictionary
country_list = gdf['Country'].unique().tolist()
country_idx = range(len(country_list))
style_dict = {}
for i in country_idx:
    countries = country_list[i]
    result = gdf[gdf['Country'] == countries]
    inner_dict = {}
    for _, r in result.iterrows():
        inner_dict[r['date']] = {'color': r['colour'], 'opacity': 0.7}
    style_dict[str(i)] = inner_dict

# creating a Geopandas dataframe for plotting
states_geom_df = gdf[['geometry']]
states_geom_gdf = gpd.GeoDataFrame(states_geom_df)
states_geom_gdf = states_geom_gdf.drop_duplicates().reset_index()

# creating the time slider map

m = folium.Map(location=[20, 0], tiles="", min_zoom=2, zoom_start=2.5, max_zoom=8, max_bounds=True)
tsm = folium.plugins.TimeSliderChoropleth(
    data=states_geom_gdf.to_json(),
    styledict=style_dict).add_to(m)

tsm = cmap.add_to(m)
cmap.caption = "Number of New cases"
ocean_tile.add_to(m)

m.save(r'webmaps/TimeSlider New cases.html')
c+=1
end_time = time.time()
total_time = end_time - map_time
total_time = time.strftime("%M:%S", time.gmtime(total_time))
print('\nthe TimeSlider New cases map was created in', total_time + '.')

# creating a color map for the New deaths
map_time = time.time()

max_colour = gdf['New deaths'].quantile(0.99)
min_colour = 0
cmap = cm.linear.OrRd_09.scale(min_colour, max_colour)
gdf['colour'] = gdf['New deaths'].map(cmap)

# creating a style dictionary
country_list = gdf['Country'].unique().tolist()
country_idx = range(len(country_list))
style_dict = {}
for i in country_idx:
    countries = country_list[i]
    result = gdf[gdf['Country'] == countries]
    inner_dict = {}
    for _, r in result.iterrows():
        inner_dict[r['date']] = {'color': r['colour'], 'opacity': 0.7}
    style_dict[str(i)] = inner_dict

# creating a Geopandas dataframe for plotting
states_geom_df = gdf[['geometry']]
states_geom_gdf = gpd.GeoDataFrame(states_geom_df)
states_geom_gdf = states_geom_gdf.drop_duplicates().reset_index()

# creating the time slider map
m = folium.Map(location=[20, 0], tiles="", min_zoom=2, zoom_start=2.5, max_zoom=8, max_bounds=True)
tsm = folium.plugins.TimeSliderChoropleth(
    data=states_geom_gdf.to_json(),
    styledict=style_dict).add_to(m)

tsm = cmap.add_to(m)
cmap.caption = "Number of New deaths"
ocean_tile.add_to(m)

m.save(r'webmaps/TimeSlider New deaths.html')
c+=1
end_time = time.time()
total_time = end_time - map_time
total_time = time.strftime("%M:%S", time.gmtime(total_time))
print('the TimeSlider New deaths map was created in', total_time + '.')

# creating an up to date choropleth map for the total covid-19 cases with a line chart
map_time = time.time()

m = folium.Map(location=[20, 0], tiles="", min_zoom=2, zoom_start=2.5, max_zoom=8, max_bounds=True)
total_cases = folium.Choropleth(geo_data=world, data=total,
                                name='total cases',
                                key_on='feature.properties.Country',
                                columns=['Country', 'Confirmed'],
                                nan_fill_color='black',
                                nan_fill_opacity=0.6,
                                fill_color='YlGn',
                                bins=6,
                                fill_opacity=1,
                                highlight=True,
                                legend_name='Number of total cases',
                                control=True,
                                )

# circle maker in layer control
fg = folium.FeatureGroup(name='Data')

for lat, lon, value, value2, name in zip(total['Lat'], total['Long'], total['Confirmed'], total['Deaths'],
                                         total['Country']):
    chart = alt.Chart(df_temp[df_temp['Country'].str.contains(name)]).mark_area(
        color="lightgreen", interpolate='step-after', line=True).encode(x='Date:T', y='New cases')
    vis1 = chart.to_json()
    folium.CircleMarker((lat, lon),
                        radius=10,
                        tooltip=('<strong>Country</strong>: ' + str(name).capitalize() + '<br>'
                                                                                         '<strong>Total Cases</strong>: ' + str(
                            value) + '<br>'
                                     '<strong>Deaths</strong>: ' + str(value2) + '<br>'),
                        popup=folium.Popup().add_child(folium.VegaLite(vis1)),
                        color='green',
                        fill_color='red',
                        fill_opacity=0.7,
                        control=False,
                        show=True).add_to(fg)

total_cases.add_to(m)
m.add_child(fg)

total_cases.geojson.add_child(folium.features.GeoJsonTooltip(['Country']))

ocean_tile.add_to(m)
Dark_bm.add_to(m)
World_Imagery_tile.add_to(m)

folium.LayerControl().add_to(m)
folium.plugins.Fullscreen().add_to(m)

m.save(r'webmaps/total covid-19 cases chart.html')
c+=1
end_time = time.time()
total_time = end_time - map_time
total_time = time.strftime("%M:%S", time.gmtime(total_time))
print('the total covid-19 cases chart map was created in', total_time + '.')

# creating an up to date choropleth map for the total covid-19 deaths with a line chart
map_time = time.time()

m = folium.Map(location=[20, 0], tiles="", min_zoom=2, zoom_start=3, max_zoom=8, max_bounds=True)

total_deaths = folium.Choropleth(geo_data=world, data=total,
                                 name='total Deaths',
                                 key_on='feature.properties.Country',
                                 columns=['Country', 'Deaths'],
                                 nan_fill_color='black',
                                 nan_fill_opacity=0.6,
                                 fill_color='OrRd',
                                 bins=7,
                                 fill_opacity=1,
                                 highlight=True,
                                 legend_name='Number of total Deaths',
                                 control=True,
                                 show=True)
# circle maker in layer control
fg = folium.FeatureGroup(name='Data')

for lat, lon, value, value2, name in zip(total['Lat'], total['Long'], total['Confirmed'], total['Deaths'],
                                         total['Country']):
    chart = alt.Chart(df_temp[df_temp['Country'].str.contains(name)]).mark_area(
        color="red", interpolate='step-after', line=True).encode(x='Date:T', y='New deaths')
    vis1 = chart.to_json()
    folium.CircleMarker((lat, lon),
                        radius=10,
                        tooltip=('<strong>Country</strong>: ' + str(name).capitalize() + '<br>'
                                                                                         '<strong>Total Cases</strong>: ' + str(
                            value) + '<br>'
                                     '<strong>Deaths</strong>: ' + str(value2) + '<br>'),
                        popup=folium.Popup().add_child(folium.VegaLite(vis1)),
                        color='green',
                        fill_color='red',
                        fill_opacity=0.7,
                        control=False,
                        show=True).add_to(fg)

total_deaths.add_to(m)
m.add_child(fg)

total_deaths.geojson.add_child(folium.features.GeoJsonTooltip(['Country']))

ocean_tile.add_to(m)
Dark_bm.add_to(m)
World_Imagery_tile.add_to(m)

folium.LayerControl().add_to(m)
folium.plugins.Fullscreen().add_to(m)

m.save(r'webmaps/total covid-19 deaths chart.html')
c+=1
end_time = time.time()
total_time = end_time - map_time
total_time = time.strftime("%M:%S", time.gmtime(total_time))
print('the total covid-19 deaths chart map was created in', total_time + '.')

# creating an up to date choropleth map for the total covid-19 cases and deaths
map_time = time.time()

m = folium.Map(location=[20, 0], tiles="", min_zoom=2, zoom_start=2.5, max_zoom=8, max_bounds=True)
total_cases = folium.Choropleth(geo_data=world, data=total,
                                name='total cases',
                                key_on='feature.properties.Country',
                                columns=['Country', 'Confirmed'],
                                nan_fill_color='black',
                                nan_fill_opacity=0.6,
                                fill_color='YlGn',
                                bins=6,
                                fill_opacity=1,
                                highlight=True,
                                legend_name='Number of total cases',
                                control=True)

total_deaths = folium.Choropleth(geo_data=world, data=total,
                                 name='total Deaths',
                                 key_on='feature.properties.Country',
                                 columns=['Country', 'Deaths'],
                                 nan_fill_color='black',
                                 nan_fill_opacity=0.6,
                                 fill_color='OrRd',
                                 bins=7,
                                 fill_opacity=1,
                                 highlight=True,
                                 legend_name='Number of total Deaths',
                                 control=True,
                                 show=False)
total_cases.geojson.add_child(folium.features.GeoJsonTooltip(['Country']))
total_deaths.geojson.add_child(folium.features.GeoJsonTooltip(['Country']))

total_cases.add_to(m)
total_deaths.add_to(m)

ocean_tile.add_to(m)
Dark_bm.add_to(m)
World_Imagery_tile.add_to(m)

folium.LayerControl().add_to(m)
folium.plugins.Fullscreen().add_to(m)

m.save(r'webmaps/total covid-19 layers.html')
c+=1
end_time = time.time()
total_time = end_time - map_time
total_time = time.strftime("%M:%S", time.gmtime(total_time))
print('the total covid-19 layers map was created in', total_time + '.')

# creating an up to date dual choropleth map the total covid-19 cases and deaths
map_time = time.time()

m = plugins.DualMap(location=[20, 0], tiles='', layout='horizontal', zoom_start=2, max_bounds=True, syncCursor=True)

# adding the total cases to the left side of the dual map
total_cases = folium.Choropleth(geo_data=world, data=total,
                                name='total cases',
                                key_on='feature.properties.Country',
                                columns=['Country', 'Confirmed'],
                                nan_fill_color='black',
                                nan_fill_opacity=0.6,
                                fill_color='YlGn',
                                bins=6,
                                fill_opacity=1,
                                highlight=True,
                                legend_name='Number of total cases',
                                control=True)
total_cases.add_to(m.m1)

## for deleting the legend of the total cases
# for key in total_cases._children:
#     if key.startswith('color_map'):
#         del (total_cases._children[key])

# adding the total deaths to the right side of the dual map
total_deaths = folium.Choropleth(geo_data=world, data=total,
                                 name='total Deaths',
                                 key_on='feature.properties.Country',
                                 columns=['Country', 'Deaths'],
                                 nan_fill_color='black',
                                 nan_fill_opacity=0.6,
                                 fill_color='OrRd',
                                 bins=7,
                                 fill_opacity=1,
                                 highlight=True,
                                 legend_name='Number of total Deaths',
                                 control=True)
total_deaths.add_to(m.m2)
## for deleting the legend of the total deaths
# for key in total_deaths._children:
#     if key.startswith('color_map'):
#         del (total_deaths._children[key])

# folium.GeoJsonTooltip(fields=['Country']).add_to(total_cases.geojson)
total_cases.geojson.add_child(folium.features.GeoJsonTooltip(['Country']))
total_deaths.geojson.add_child(folium.features.GeoJsonTooltip(['Country']))

ocean_tile.add_to(m)
World_Imagery_tile.add_to(m)
Dark_bm.add_to(m)

folium.LayerControl().add_to(m)

m.save(r'webmaps/total cases to death dual map.html')
c+=1
end_time = time.time()
total_time = end_time - map_time
total_time = time.strftime("%M:%S", time.gmtime(total_time))
print('the total cases to death dual map was created in', total_time + '.')

end_time = time.time()
total_time = end_time - start_time
total_time = time.strftime("%M:%S", time.gmtime(total_time))
print('\nThe program created', c, 'maps. \n' + 'Total Execution time is:', total_time + '.')
# exit()
