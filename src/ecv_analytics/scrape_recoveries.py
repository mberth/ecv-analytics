import re
import sys
import pandas as pd
import requests
from bs4 import BeautifulSoup


WIKIPEDIA = 'https://en.wikipedia.org'
COVID_PANDEMIC_URL = '%s/w/index.php?title=COVID-19_pandemic_in_{}' % WIKIPEDIA


def extract_history(parsed):
    """Return a links and timestmps for a history page."""
    history = parsed.find(id="pagehistory").find_all("li")
    answer = []
    for entry in history:
        link = entry.find("a", class_="mw-changeslist-date")
        if link:
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
    return extract_recovered_from_html(page.text, url=url)


def cleanup_number(text):
    parts = re.split(r"[^0-9,]", text)
    digits = parts[0].replace(",", "")
    if digits == '':
        return None
    return int(digits)


def extract_recovered_from_html(text, url=None):
    if 'Recovered' not in text:
        # Some older versions
        return None
    tables = pd.read_html(text, attrs={'class': 'infobox'})
    if len(tables) != 1:
        print(f"Warning: taking the first infobox at {url}.")
    table = tables[0]
    table.columns = ['name', 'value']
    try:
        value = table.set_index('name').loc['Recovered'].value
    except KeyError:
        # print('Recovered not found for ' + url)
        # print(table)
        return None
    return cleanup_number(value)


def time_series_recovered(wiki_name, name=None, iso_code=None, limit=5):
    print(f"Fetching {wiki_name}")
    url = COVID_PANDEMIC_URL.format(
        wiki_name) + f'&limit={limit}&action=history'
    print("Analyzing page history at {}".format(url))
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
