import pandas as pd
import importlib.resources as pkg_resources

from ecv_analytics import data
from ecv_analytics.scrape_recoveries import time_series_recovered

states = pd.read_csv(pkg_resources.open_text(data, "wikipedia_ISO_3166-2_US.csv"))

all_states = []

restart = 'US-KS'
restart_index = list(states.Iso_3166_2).index(restart)

for index, row in states.iloc[restart_index:].iterrows():
    time_series = time_series_recovered(row['Wikipedia_Name'],
        name=row['Name'],
        iso_code=row['Iso_3166_2'], limit=500)
    filename = 'time_servies_recovered_wikipedia_{}.csv'.format(
        row['Iso_3166_2'])
    time_series.to_csv(filename)
    all_states.append(time_series)

pd.concat(all_states).to_csv('time_servies_recovered_wikipedia.csv')
