'''This program is designed to take covid-19 data and wrold population data and a shapefile
from the internet and wrangle the data then produce webmaps in html '''


# resorces 
# the covid-19 data provided by johns-hopkins-university 
# https://github.com/CSSEGISandData/COVID-19.git  

# for the world population
# https://worldpopulationreview.com/countries

# for the shapefile 
# https://drive.google.com/drive/folders/16Y3vUcsbv8trPQ4WnbA-5sf4o0iAdPyq?usp=sharing


import os , wget
from datetime import datetime
import geojson
import geopandas as gpd
import pandas as pd
import numpy as np
import folium
from folium import plugins
import matplotlib.pyplot as plt
import seaborn as sns

# these python libraries are extra and only for future improvment of the program

# import altair as alt
# import json
# import plotly.express as px
# import plotly.graph_objs as go
# from plotly.subplots import make_subplots
# from plotly.offline import iplot,init_notebook_mode
# init_notebook_mode()

# creating a folder to host the downloaded data
if not os.path.exists('data'):
    os.mkdir('data')


# getting recuired files from the internet
# if the shape file and population exists it will skip it because it is a static file with no time cahnging effect
if not os.path.isfile(r'world_map.shp'):
    urls = ['https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv', 
            'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv',
            'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv']

else:
    urls = ['https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv', 
            'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv',
            'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv',
            'https://github.com/samer199817/covid-19_webmaps_AAST/blob/def2ea49e6bbc3aaad03c10089ad42c0c457645b/input/csvData.csv',
            'https://github.com/samer199817/covid-19_webmaps_AAST/blob/def2ea49e6bbc3aaad03c10089ad42c0c457645b/input/World_Map.shp',
            'https://github.com/samer199817/covid-19_webmaps_AAST/blob/def2ea49e6bbc3aaad03c10089ad42c0c457645b/input/World_Map.cpg',
            'https://github.com/samer199817/covid-19_webmaps_AAST/blob/def2ea49e6bbc3aaad03c10089ad42c0c457645b/input/World_Map.dbf',
            'https://github.com/samer199817/covid-19_webmaps_AAST/blob/def2ea49e6bbc3aaad03c10089ad42c0c457645b/input/World_Map.prj',
            'https://github.com/samer199817/covid-19_webmaps_AAST/blob/def2ea49e6bbc3aaad03c10089ad42c0c457645b/input/World_Map.sbn',
            'https://github.com/samer199817/covid-19_webmaps_AAST/blob/def2ea49e6bbc3aaad03c10089ad42c0c457645b/input/World_Map.sbx',
            'https://github.com/samer199817/covid-19_webmaps_AAST/blob/def2ea49e6bbc3aaad03c10089ad42c0c457645b/input/World_Map.shx']

if os.path.isfile(r'data/time_series_covid19_confirmed_global.csv'): os.unlink(r'data/time_series_covid19_confirmed_global.csv')
if os.path.isfile(r'data/time_series_covid19_deaths_global.csv'): os.unlink(r'data/time_series_covid19_deaths_global.csv')
if os.path.isfile(r'data/time_series_covid19_recovered_global.csv'): os.unlink(r'data/time_series_covid19_recovered_global.csv')
for url in urls: filename = wget.download(url,out='data')


# inserting the required files
df_confirmed = pd.read_csv(r'time_series_covid19_confirmed_global.csv')
df_death = pd.read_csv(r'time_series_covid19_deaths_global.csv')
df_recovered = pd.read_csv(r'time_series_covid19_recovered_global.csv')
world = gpd.read_file(r'input\World_Map.shp')
pop = pd.read_csv(r'input\csvData.csv')

# saving the Latitude and longitude 
df_cor = df_confirmed[['Country/Region','Lat','Long']]


# getting the dates
dates = df_confirmed.columns[4:]

# melt dataframes into pivot like dataframes
df_confirmed_melt = df_confirmed.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], 
                            value_vars=dates, var_name='Date', value_name='Confirmed')

df_death_melt = df_death.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], 
                            value_vars=dates, var_name='Date', value_name='Deaths')

df_recovered_melt = df_recovered.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], 
                            value_vars=dates, var_name='Date', value_name='Recovered')


# mergging dataframes to get all values togther
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
df = df[df['Province/State'].str.contains('Recovered')!=True]

# removing county wise data to avoid double values
df = df[df['Province/State'].str.contains(',')!=True]

# creating an Active column for analysis 
df['Active'] = df['Confirmed'] - df['Deaths'] - df['Recovered']

cols = ['Confirmed', 'Deaths', 'Recovered', 'Active']
# giving all the null values (0)
df[cols] = df[cols].fillna(0)


# Groupping by day, country for improving the quality of the data 
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

full_grouped['New cases'] = full_grouped['New cases'].apply(lambda x: 0 if x<0 else x)

full_grouped = full_grouped.groupby(['Date','Country/Region'])['Confirmed', 'Deaths', 'Recovered','New cases', 'New deaths', 'New recovered'].sum().reset_index()

# mergging dataframes for adding latitude and longitude 
full_grouped = pd.merge(left=full_grouped, right=df_cor, how='left', on=['Country/Region'])

# renaming columns
full_grouped.rename(columns={'Country/Region':'Country'},inplace=True)

full_grouped = full_grouped[full_grouped.Country!='Diamond Princess']
full_grouped = full_grouped[full_grouped.Country!='MS Zaandam']
full_grouped = full_grouped[full_grouped.Country!='Summer Olympics 2020']

# droping two null values in china and in canada and renaming DataFrame
df = full_grouped.dropna()



# dropping islands that can affect the data
df = df[df.Country!='Diamond Princess']
df = df[df.Country!='MS Zaandam']
df = df[df.Country!='Summer Olympics 2020']
# this two are extra from another column but i left them just for remmbering if i wanted to use them again
# df = df[df.State!='Grand Princess'] 
# df = df[df.State!='Diamond Princess']

# This places doesn't have population data 
# Åland Islands, Bouvet Island, British Indian Ocean Territory, Cocos (Keeling) Islands, French Southern and Antarctic Lands, 
# Guernsey, Heard Island and McDonald Islands, Jersey islands, Netherlands Antilles, Norfolk Island, Green land
# Pitcairn Islands, Saint Helena, Svalbard, United States Minor Outlying Islands, Wallis and Futuna Islands


# the population data didn't match the Country names 
## editing the population data names to match the Country names
pop.replace('Bouvet Island', '', inplace = True)
pop.replace('Brunei', 'Brunei Darussalam', inplace = True)
pop.replace('Myanmar', 'Burma', inplace = True)
pop.replace('Darussalam', '', inplace = True)
pop.replace('DR Congo', 'Democratic Republic of the Congo', inplace = True)
pop.replace('Republic of the Congo', 'Congo', inplace = True)
pop.replace('Ivory Coast', "Cote d'Ivoire", inplace = True)
pop.replace('Falkland Islands', 'Falkland Islands (Malvinas)', inplace = True)
pop.replace('Vatican City', 'Holy See (Vatican City)', inplace = True)
pop.replace('Iran', 'Iran (Islamic Republic of)', inplace = True)
pop.replace('North Korea', "Korea, Democratic People's Republic of", inplace = True)
pop.replace('South Korea', 'Korea, Republic of', inplace = True)
pop.replace('Laos', "Lao People's Democratic Republic", inplace = True)
pop.replace('Libya', 'Libyan Arab Jamahiriya', inplace = True)
pop.replace('Micronesia', 'Micronesia, Federated States of', inplace = True)
pop.replace('Moldova', 'Republic of Moldova', inplace = True)
pop.replace('Eswatini', 'Swaziland', inplace = True)
pop.replace('Syria', 'Syrian Arab Republic', inplace = True)
pop.replace('North Macedonia', 'The former Yugoslav Republic of Macedonia', inplace = True)
pop.replace('Tanzania', 'United Republic of Tanzania', inplace = True)
pop.replace('Vietnam', 'Viet Nam', inplace = True)

# matching the column's name for a better match
pop.rename(columns={'name':'Country'},inplace=True)
world.rename(columns={'NAME':'Country'},inplace=True)

# Merging the 'pop' with 'world' geopandas geodataframe
world = world.merge(pop,on=['Country'])

# the shapefile data didn't match the DataFrame
## editing the Country names to match the DataFrame
world.replace('Viet Nam', 'Vietnam', inplace = True)
world.replace('Brunei Darussalam', 'Brunei', inplace = True)
world.replace('Cape Verde', 'Cabo Verde', inplace = True)
world.replace('Democratic Republic of the Congo', 'Congo (Kinshasa)', inplace = True)
world.replace('Congo', 'Congo (Brazzaville)', inplace = True)
world.replace('Czech Republic', 'Czechia', inplace = True)
world.replace('Swaziland', 'Eswatini', inplace = True)
world.replace('Iran (Islamic Republic of)', 'Iran', inplace = True)
world.replace('Korea, Republic of', 'Korea, South', inplace = True)
world.replace("Lao People's Democratic Republic", 'Laos', inplace = True)
world.replace('Libyan Arab Jamahiriya', 'Libya', inplace = True)
world.replace('Republic of Moldova', 'Moldova', inplace = True)
world.replace('The former Yugoslav Republic of Macedonia', 'North Macedonia', inplace = True)
world.replace('Syrian Arab Republic', 'Syria', inplace = True)
world.replace('Taiwan', 'Taiwan*', inplace = True)
world.replace('United Republic of Tanzania', 'Tanzania', inplace = True)
world.replace('United States', 'US', inplace = True)
world.replace('Palestine', 'West Bank and Gaza', inplace = True)

# Merging the 'data' with 'world' geopandas geodataframe
merge = world.merge(df,on=['Country'])


# adding a population column and adding the data to column based on the date
merge['Population'] = np.where(merge.Date<='2020-12-31',merge.pop2020,merge.pop2021)

# dropping the pop2020 and pop2021 and rearranging the columns and renaming the data frame 
gdf = merge[['Country','Date','New cases','New deaths','Confirmed','Deaths','Population','Rank','GrowthRate','area','Density','Lat','Long','geometry']]

# creating a total dataframe for the analysis
total = gdf[gdf['Date']==str(gdf['Date'].tolist())[-22:-12]][['Country','Confirmed','Deaths','Population','Rank','GrowthRate','area','Density','Lat','Long','geometry']]
total
total['n_Confirmed'] = total['Confirmed'] / total['Confirmed'].sum()
total.to_file('total.shp')
# creating a Geojson file 
geoj=total.to_json()

# creating a folder to save the webmaps
if os.path.exists(r'webmaps'):
    os.rmdir(r'webmaps')
os.mkdir(r'webmaps')

# plot

# creating an up to date choropleth map the total covid-19 cases 
m = folium.Map(location=[20, 0], tiles= "stamenwatercolor",min_zoom=2, zoom_start=2.5, max_zoom=8,max_bounds=True)
total_cases = folium.Choropleth(geo_data=geoj, data=total,
                                name='total confirmed cases',
                                key_on='feature.properties.Country',
                                columns=['Country','Confirmed'],
                                nan_fill_color='black',
                                nan_fill_opacity=0.6,
                                fill_color='YlGn',
                                bins=[2,75000,270000,660000,1100000,4000000,6800000,45000000],
                                fill_opacity=1,
                                highlight=True,
                                legend_name='Number of total Confirmed cases')

total_cases.geojson.add_child(folium.features.GeoJsonTooltip(['Country','Confirmed','Deaths']))
total_cases.add_to(m)
m.save(r'webmaps/total covid-19 cases')

# creating an up to date choropleth map the total covid-19 deaths 
m = folium.Map(location=[20, 0], tiles= "stamenwatercolor",min_zoom=2, zoom_start=2.5, max_zoom=8,max_bounds=True)
total_deaths = folium.Choropleth(geo_data=geoj, data=total,
                                name='total Deaths',
                                key_on='feature.properties.Country',
                                columns=['Country','Deaths'],
                                nan_fill_color='black',
                                nan_fill_opacity=0.6,
                                fill_color='OrRd',
                                bins=[0,2000,10000,20000,35000,75000,350000,690000],
                                fill_opacity=1,
                                highlight=True,
                                legend_name='Number of total Deaths')

total_deaths.geojson.add_child(folium.features.GeoJsonTooltip(['Country','Confirmed','Deaths']))
total_deaths.add_to(m)
m.save(r'webmaps/total covid-19 deaths')

# creating an up to date dual choropleth map the total covid-19 cases and deaths
md = plugins.DualMap(location=[20,0], tiles='stamenwatercolor',layout='horizontal', zoom_start=2,max_bounds=True)

# adding the total cases to the left side of the dual map
total_cases.add_to(md.m1)

# for deleting the legend of the total cases  
for key in total_cases._children:
    if key.startswith('color_map'):
        del(total_cases._children[key])

# adding the total deaths to the right side of the dual map
total_deaths.add_to(md.m2) 

# for deleting the legend of the total deaths
for key in total_deaths._children:
    if key.startswith('color_map'):
        del(total_deaths._children[key])

md.save('total casses to death dualmap.html')

# wrangling the heatmap and normalising the new cases column
heatmap_data = gdf 
heatmap_data['Lat'] = heatmap_data['Lat'].astype(float)
heatmap_data['Long'] = heatmap_data['Long'].astype(float)
heatmap_data['New cases'] = heatmap_data['New cases'] / heatmap_data['New cases'].sum()
heatmap_data = heatmap_data[['Lat', 'Long','New cases','Date']]
heatmap_data['Date'] = heatmap_data['Date'].sort_values(ascending=True)
data = []
time=[]
for i, v in heatmap_data.groupby('Date'):
    time.append(str(i).split(' ')[0])
    data.append([[row['Lat'], row['Long'], row['New cases']] for i, row in v.iterrows()])

# heatmap with time for the new cases
m = folium.Map(location=[20, 0], tiles= "CartoDB Dark_Matter",min_zoom=2, zoom_start=2, max_zoom=3,max_bounds=True)

hm_new = plugins.HeatMapWithTime(data , 
                             index=time,
                             auto_play=True,
                             display_index=True,
                             max_opacity=0.8)

hm_new.add_to(m)
m.save(r'webmaps/heatmap covid-19 new cases.html')

# wrangling the heatmap and normalising the deaths column
heatmap_data = gdf 
heatmap_data['Lat'] = heatmap_data['Lat'].astype(float)
heatmap_data['Long'] = heatmap_data['Long'].astype(float)
heatmap_data['New deaths'] = heatmap_data['New deaths'] / heatmap_data['New deaths'].sum()
heatmap_data = heatmap_data[['Lat', 'Long','New deaths','Date']]
heatmap_data['Date'] = heatmap_data['Date'].sort_values(ascending=True)
data = []
time=[]
for i, v in heatmap_data.groupby('Date'):
    time.append(str(i).split(' ')[0])
    data.append([[row['Lat'], row['Long'], row['New deaths']] for i, row in v.iterrows()])

# heatmap with time for the deaths
hm_death = plugins.HeatMapWithTime(data , 
                             index=time,
                             auto_play=True,
                             display_index=True,
                             max_opacity=0.8)
hm_death.add_to(m)


# creating a new dual map for the covid-19 new cases and deaths as a heatmap
md = plugins.DualMap(location=[20,0], tiles='CartoDB Dark_Matter',layout='horizontal', zoom_start=2.5,max_bounds=True)

# adding the new cases heatmap to the left side of the dual map
hm_new.add_to(md.m1)

# adding the new deaths heatmap to the right side of the dual map
hm_death.add_to(md.m2)

# exit()