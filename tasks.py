import os
import shutil

from invoke import task
import pathlib

ROOT_DIR = os.getcwd()
BUILD_DIR = pathlib.Path("build")
REPO = "https://github.com/obuchel/classification"

def reset_dir():
    os.chdir(ROOT_DIR)

@task
def copy_index(c):
    """Copy the top-level index file to the site."""
    site = BUILD_DIR / 'site'
    shutil.copy("source/index.html", site)

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
    shutil.copy("source/us-counties/index.html", site)


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
