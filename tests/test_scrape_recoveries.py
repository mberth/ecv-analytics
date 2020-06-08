from ecv_analytics.scrape_recoveries import extract_recovered_from_html
import importlib.resources as pkg_resources
from . import html_examples

def test_recovered_extra_text():
    """Parse this correctly:
        Recovered	4481 ([Johns Hopkins University
    """
    page = pkg_resources.read_text(html_examples, 'California_wikipedia_page_2020-04-25.html')
    assert extract_recovered_from_html(page) == 4481

