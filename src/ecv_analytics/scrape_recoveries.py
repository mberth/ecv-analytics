import sys
import pandas as pd
import requests
from bs4 import BeautifulSoup

WIKIPEDIA = 'https://en.wikipedia.org'
COVID_PANDEMIC_URL = '%s/w/index.php?title=COVID-19_pandemic_in_{}' % WIKIPEDIA

states = pd.read_csv("wikipedia_ISO_3166-2_US.csv")


def extract_history(parsed):
    """Return a links and timestmps for a history page."""
    history = parsed.find(id="pagehistory").find_all("li")
    answer = []
    for entry in history:
        link = entry.find("a", class_="mw-changeslist-date")
        ts = pd.to_datetime(link.text, dayfirst=True)
        answer.append({'href': link["href"], 'timestamp': ts})
    return answer


def daily_versions(parsed):
    """Return a DataFrame with href, timestamp for the most recent version of each day.

    Example page:
    https://en.wikipedia.org/w/index.php?title=COVID-19_pandemic_in_Wisconsin&oldid=961203717
    """
    updates = pd.DataFrame(extract_history(parsed))
    # Keep only the most recent update of each day
    updates = updates.groupby(updates.timestamp.dt.date).first()
    # TODO: Check if we're all getting these dates in the same timezone,
    #       no matter if we run the script in Europe or in the USA
    return updates


def extract_recovered(url):
    """Return the Recovered number from the Infobox."""
    print(url)
    page = requests.get(url)
    if page.status_code != 200:
        return None
    if 'Recovered' not in page.text:
        # Some older versions
        return None
    tables = pd.read_html(page.text, attrs={'class': 'infobox'})
    assert len(tables) == 1, "There should be only one Infobox."
    table = tables[0]
    table.columns = ['name', 'value']
    try:
        value = int(table.set_index('name').loc['Recovered'].value)
    except KeyError:
        # print('Recovered not found for ' + url)
        # print(table)
        return None
    return value


def time_series_recovered(wiki_name, name=None, iso_code=None, limit=5):
    print(f"Fetching {wiki_name}")
    url = COVID_PANDEMIC_URL.format(
        wiki_name) + f'&limit={limit}&action=history'
    page = requests.get(url)
    if page.status_code != 200:
        print(f"Bad HTTP status for {url}")
        return None
    parsed = BeautifulSoup(page.text, "html.parser")
    versions = daily_versions(parsed)
    versions.index.names = ['date']
    versions['Iso_3166_2'] = iso_code
    versions['Name'] = name
    versions['Recovered'] = versions.href.map(
        lambda url: extract_recovered(WIKIPEDIA + url))
    versions['href'] = WIKIPEDIA + versions['href']
    versions.insert(len(versions.columns) - 1, 'href', versions.pop('href'))
    versions.rename(columns={'href': 'Source'})
    return versions


all_states = [
    time_series_recovered(row['Wikipedia_Name'], name=row['Name'],
        iso_code=row['Iso_3166_2'], limit=500)
    for index, row in states.iloc[:].iterrows()
]

pd.concat(all_states).to_csv('time_servies_recovered_wikipedia.csv')
