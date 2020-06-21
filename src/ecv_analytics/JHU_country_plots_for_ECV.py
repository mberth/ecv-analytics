#!/usr/bin/env python
# coding: utf-8

# # Automated country classification

# This file is meant to take in JHU data for countries, then produce simple plots for the ECV website

# In[26]:

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

FIGURES_PATH = Path(r'build/site/countries/figures')
"""Where the charts are saved."""

FIGURES_PATH.mkdir(parents=True, exist_ok=True)

# ## Get data from GitHub

# Use 3 dataframes to restore the data seperately. The output is the the update time, if should be one day ago (usually by morning EST, yesterday's full data is updated). If not, please wait until the output of this cell is yesterday.

# In[27]:


df = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
focus = df.copy().drop(['Lat','Long'], axis=1).set_index(['Country/Region','Province/State'])
confirm = focus.groupby('Country/Region').sum().T

df = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')
focus = df.copy().drop(['Lat','Long'], axis=1).set_index(['Country/Region','Province/State'])
death = focus.groupby('Country/Region').sum().T

df = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv')
focus = df.copy().drop(['Lat','Long'], axis=1).set_index(['Country/Region','Province/State'])
recover = focus.groupby('Country/Region').sum().T

for i in [confirm, recover, death]:
    i.index = pd.to_datetime(i.index)

date = pd.to_datetime("today").strftime('_%m_%d')
print('Latest update time is:',date)

confirm['time'] = pd.to_datetime(confirm.index)
confirm.index = confirm.time.dt.strftime('%m/%d')
confirm.drop('time', axis=1, inplace=True)


# ## Defining which counrties to leave out

# In[28]:


do_not_include = ['Antigua and Barbuda', 'Angola', 'Benin', 'Botswana', 
                  'Brunei', 'Burundi', 'Cabo Verde', 'Chad', 'Comoros', 
                  'Congo (Brazzaville)', 'Congo (Kinshasa)', "Cote d'lvoire", 'Central African Republic',
                  'Diamond Princess', 'Dominica', 'Equatorial Guinea',
                  'Eritrea', 'Ecuador', 'Eswatini', 'Fiji', 'Gabon', 
                  'Gambia', 'Ghana', 'Grenada', 'Guinea', 'Guinea-Bissau',
                  'Guyana', 'Laos', 'Lesotho', 'Liberia', 'Libya', 'Madagascar',
                  'Malawi', 'Maldives', 'Mauritania', 'Mozambique',
                  'MS Zaandam', 'Namibia', 'Nicaragua', 'Papua New Guinea',
                  'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia', 
                  'Saint Vincent and the Grenadines', 'Sao Tome and Principe',
                  'Seychelles', 'Sierra Leone', 'South Sudan', 'Suriname', 'Syria', 
                  'Tanzania', 'Timor-Leste', 'Togo', 'Uganda', 'West Bank and Gaza',
                  'Western Sahara', 'Yemen', 'Zambia', 'Zimbabwe']


# ## Update country plots

# In[33]:


winning = 0 
nearly_there = 0 
needs_action = 0

for j, country in enumerate(confirm.iloc[-1].sort_values(ascending=False).index[:]):

    #if you want to choose one single country, use this. If not, comment it out
    """
    if country ==  'France':
        pass
    else: 
        continue
    """
    
    #choosing offsets
    if country == 'China':
        offset = 0
    elif country == 'Korea, South':
        offset = 10
    else:
        offset = 30    



    #leaving out countries which haven't been vetted, or have bad data
    if country in do_not_include:
        continue
        
    #choosing font sizes for the figure title
    if len(country) > 14:
        font_size = 100
    else: 
        font_size = 130        
        
        
    focus =  confirm.loc[:,[country]].copy()[offset:]
    focus['new'] = focus[country] - focus[country].shift(1)
    
    # Correcting some data
    if country == 'France':
        focus.at['06/02', 'new'] = 0
        focus.at['06/04', 'new'] = 767
    
    fig, ax=plt.subplots(nrows=1, ncols=1, figsize=(18,16))
    # ax.plot(focus.index, focus['new'], label= country, alpha=0, c='black', linewidth=6)
    # ax.scatter(focus.index, focus.new, c='orangered',s=20, label='')

    #computing the average over the last d days
    d = 7 #the number of recent days to average over for new cases/day     
    avg=int(focus['new'][len(focus)-d:].sum()/d) #compute average new cases for the last d days

    #averaging window
    window = 7
    focus['average'] = focus['new'].rolling(window=window, min_periods=1, center=True).mean()
    
    #choosing colors
    n_0 = 20
    f_0 = 0.5
    f_1 = 0.2
    peak = focus['average'].max()
    
    if avg <= n_0*f_0 or avg <= n_0 and avg <= f_0*peak:
        color = 'green'
        winning += 1
    elif avg <= 1.5*n_0 and avg <= f_0*peak or avg <= peak*f_1:
        color = 'orange'
        nearly_there += 1
    else:
        color = 'red'
        needs_action += 1

    #window = averaging window
    window = 7
    focus['average'] = focus['new'].rolling(window=window, min_periods=1, center=True).mean()
    ax.plot(focus.index, focus.average, lw=14, alpha=2, c=color)
    ax.tick_params(labelsize=40) #either 40 or 50 
    ax.set_yticklabels([])

    #removing axes
    for axis in ['bottom']:
      ax.spines[axis].set_linewidth(10)
    for axis in ['right','top', 'left']:
      ax.spines[axis].set_linewidth(0)


    #correcting country names
    if country == 'Taiwan*':
        country = 'Taiwan'
    if country == 'Korea, South':
        country = 'South Korea'
    if country == 'United Arab Emirates':
        country = 'U.A.E.'
    if country == 'Bosnia and Herzegovina':
        country = 'Bosnia'

    #some names are too long
    if len(country) > 14:
        font_size = 100
    else: 
        font_size = 130



    plt.title(country, y=-.2, fontsize=font_size) #fontsize = 130 typically, long names -> 100
    total=int(focus['new'].sum()) #compute total cases
    avg=int(focus['new'][len(focus)-d:].sum()/d) #compute average new cases for the last d days
    #print(avg)
    #print(focus['new'][len(focus)-d:])

    plt.suptitle("total cases: {:,}\nrecent new/day: {:,}".format(total, avg), y=-0.03, fontsize=60, color='grey')
    #plt.suptitle("total cases: {:,}".format(total), y=-0.03, fontsize=60, color='grey')

    plt.tight_layout()
    ax.tick_params(axis='x', pad=10)
    ax.xaxis.set_major_locator(plt.MaxNLocator(9))
    (FIGURES_PATH / color).mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURES_PATH / color / ('%s.png' % (country + date)), dpi=300, bbox_inches='tight', pad_inches=1)
    # plt.show()
print('winning = ' + str(winning))
print('nearly there = ' + str(nearly_there))
print('needs action = ' + str(needs_action))
print('not listed: ' + str(len(do_not_include)))


