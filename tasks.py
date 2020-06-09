import sys
if 'src' not in sys.path:
    # https://stackoverflow.com/questions/10095037/why-use-sys-path-appendpath-instead-of-sys-path-insert1-path
    sys.path.insert(1, "src")

import datetime as dt
import importlib.resources as pkg_resources
import os
import pathlib
import shutil

import pandas as pd
from invoke import task

from ecv_analytics import data
from ecv_analytics.scrape_recoveries import time_series_recovered

ROOT_DIR = os.getcwd()
BUILD_DIR = pathlib.Path("build")
WIKIPEDIA_RECOVERED = BUILD_DIR / 'scraping/wikipedia-recovered'

REPO = "https://github.com/obuchel/classification"

def reset_dir():
    os.chdir(ROOT_DIR)


@task
def copy_index(c):
    """Copy the top-level index file to the site."""
    site = BUILD_DIR / 'site'
    shutil.copy("site/index.html", site)


@task(post=[copy_index])
def copy_us_counties(c):
    reset_dir()
    site = BUILD_DIR / 'site/us-counties'
    repo = BUILD_DIR / 'repos/classification'
    site.mkdir(parents=True, exist_ok=True)
    c.run(f"rsync -a {repo}/output {site}")
    files = [
        # HTML pages
        'classification_map.html', 'classification_map2.html',
        # JS files
        'map_impl.js', 'map_impl2.js',
        # Icons
        'green.png', 'orange.png', 'red.png', 'yellow.png',
        # geo data
        'counties5.json', 'states5.json', ]
    for file in files:
        shutil.copy(repo / file, site)
    shutil.copy("site/us-counties/index.html", site)


@task(post=[copy_us_counties])
def us_counties(c):
    reset_dir()
    repos = BUILD_DIR / "repos"
    repos.mkdir(parents=True, exist_ok=True)
    if os.path.exists(repos / "classification"):
        os.chdir(repos / "classification")
        c.run("git pull")
    else:
        os.chdir(repos)
        c.run("git clone {}".format(REPO))
        os.chdir("classification")
    print(os.getcwd())
    c.run("python prepare_classification_counties_final.py", echo=True)


@task
def scrape_recovered_from_wikipedia(c, restart='US-AL',
                                    output=WIKIPEDIA_RECOVERED):
    """Scrape time series of recovered cases from historic versions of Wikipedia pages.

    :param restart Restart scraping at a state, given by its ISO code, e.g. US-VA for Virginia
    :param output Write CSV files into this directory, defaults to 'build/scraping/wikipedia-recovered/YYYY-MM-DD_HHMM'

    Example: https://en.wikipedia.org/w/index.php?title=COVID-19_pandemic_in_Wisconsin
    """
    outdir = pathlib.Path(output)
    outdir.mkdir(parents=True, exist_ok=True)
    rundir = outdir / dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    rundir.mkdir(parents=True, exist_ok=True)
    print("Writing output to {}".format(rundir))

    states = pd.read_csv(pkg_resources.open_text(data, "wikipedia_ISO_3166-2_US.csv"))
    all_states = []
    restart_index = list(states.Iso_3166_2).index(restart)
    for index, row in states.iloc[restart_index:].iterrows():
        if pd.isna(row['Wikipedia_Name']):
            continue
        time_series = time_series_recovered(row['Wikipedia_Name'],
                                            name=row['Name'],
                                            iso_code=row['Iso_3166_2'], limit=500)
        filename = 'time_servies_recovered_wikipedia_{}.csv'.format(row['Iso_3166_2'])
        time_series.to_csv(rundir / filename)
        all_states.append(time_series)
    pd.concat(all_states).to_csv(rundir / 'time_servies_recovered_wikipedia.csv')


@task
def review_scraped_recoveries(c, csvdir=None):
    """Transform scraped data for Recovered into heatmaps in html and Excel format.

    :param csvdir The directory with CSV files of scraped wikipedia data for Recovered cases.
    """
    states = pd.read_csv(pkg_resources.open_text(data, "wikipedia_ISO_3166-2_US.csv"))
    assert os.path.exists(csvdir), "CSV directory not found"
    location = pathlib.Path(csvdir)
    filenames = [location / f"time_servies_recovered_wikipedia_{statecode}.csv" for statecode in states.Iso_3166_2]
    filenames = [fname for fname in filenames if os.path.isfile(fname)]

    all_states = pd.concat([pd.read_csv(fname) for fname in filenames])
    all_states = all_states[['date', 'Name', 'Recovered']].sort_values('date', ascending=False)
    pivoted = all_states.pivot(index='Name', columns='date')
    pivoted = pivoted.round().fillna(-1)
    # Reverse column order: most recent days should be left.
    pivoted = pivoted.iloc[:, ::-1]
    # Heat map, see https://stackoverflow.com/questions/29432629/plot-correlation-matrix-using-pandas/50703596#50703596
    # Alternative: cmap='coolwarm'
    heatmap = pivoted.style.background_gradient(cmap='viridis', axis=1).set_na_rep('').set_precision(0)
    print("Writing heatmaps to {}".format(location))
    with open(location / 'heatmap.html', 'w') as file:
        file.write(heatmap.render().replace('>-1</td>', '></td>'))
    heatmap.to_excel(location / 'heatmap.xlsx')

