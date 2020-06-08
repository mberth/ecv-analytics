from ecv_analytics.scrape_recoveries import (extract_recovered_from_html,
                                             cleanup_number)
import importlib.resources as pkg_resources
from . import html_examples

def test_recovered():
    # Recovered	11,395
    check_recovered('Alabama_wikipedia_page_2020-06-07.html', 11395)
    # No entry for Recovered
    check_recovered('Arizona_wikipedia_page_2020-06-07.html', None)
    # Recovered	4481 ([Johns Hopkins University
    check_recovered('California_wikipedia_page_2020-04-25.html', 4481)
    # 5,010[citation needed]
    check_recovered('Florida_wikipedia_page_2020-05-05.html', 5010)


def check_recovered(html, expected, message=''):
    page = pkg_resources.read_text(html_examples, html)
    assert extract_recovered_from_html(page) == expected, message


def test_cleanup_number():
    assert cleanup_number('11395') == 11395
    assert cleanup_number('4481 ([Johns Hopkins University') == 4481
    assert cleanup_number('5,010[citation needed]') == 5010
    assert cleanup_number('') == None
