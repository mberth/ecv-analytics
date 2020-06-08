from ecv_analytics.scrape_recoveries import extract_recovered
import importlib.resources as pkg_resources

def test_dummy():
    assert 2 + 2 == 4

    from . import \
        html_examples  # relative-import the *package* containing the templates
    #
    page = pkg_resources.read_text(html_examples, 'California_wikipedia_page_2020-04-25.html')
    assert "Recovered" in page
