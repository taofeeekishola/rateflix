"""Pages anyone can see: home, filters, search and movie pages."""
import re

import pytest

from conftest import IDS


def card_titles(html):
    return re.findall(r'<h3 class="rf-card__title">([^<]+)</h3>', html)


@pytest.mark.parametrize('page', ['/', '/search/', '/search/?q=inside', '/user/login/', '/user/signup/', '/admin/login/'])
def test_public_pages_load(client, page):
    assert client.get(page).status_code == 200


def test_home_lists_live_movies_only(client):
    titles = card_titles(client.get('/').get_data(as_text=True))
    assert 'Inside Out 2' in titles and 'Quiet Drama' in titles
    assert 'Alice Pending Movie' not in titles


def test_filters_can_be_combined(client):
    html = client.get('/ajax/movie/filter/?genre={animation}&year=2024'.format(**IDS)).get_data(as_text=True)
    assert card_titles(html) == ['Inside Out 2']
    html = client.get('/ajax/movie/filter/?genre={animation}&year=2023'.format(**IDS)).get_data(as_text=True)
    assert card_titles(html) == [] and 'No movies match' in html


def test_filters_in_the_address_fill_the_page(client):
    html = client.get('/?studio={other_studio}'.format(**IDS)).get_data(as_text=True)
    assert card_titles(html.split('id="movies"')[1]) == ['Quiet Drama']


def test_junk_filter_values_are_ignored(client):
    assert client.get('/ajax/movie/filter/?year=abc&genre=x').status_code == 200


def test_search_finds_titles_in_any_case(client):
    assert card_titles(client.get('/search/?q=INSIDE').get_data(as_text=True)) == ['Inside Out 2']


def test_search_treats_percent_as_a_normal_character(client):
    html = client.get('/search/?q=%25').get_data(as_text=True)
    assert card_titles(html) == [] and 'No movies found' in html


def test_search_hides_pending_movies(client):
    assert card_titles(client.get('/search/?q=pending').get_data(as_text=True)) == []


def test_movie_page_loads(client):
    html = client.get('/movie/info/{cartoon}'.format(**IDS)).get_data(as_text=True)
    assert 'Inside Out 2' in html and 'Test Producer' in html and 'Actor One' in html


def test_unknown_movie_gives_a_404_page(client):
    response = client.get('/movie/info/999')
    assert response.status_code == 404 and b'Page not found' in response.data


def test_movie_titles_are_escaped_in_filter_results(client):
    from rateflix.models import Movie, db
    db.session.get(Movie, IDS['cartoon']).movie_title = '<script>alert(1)</script>'
    db.session.commit()
    html = client.get('/ajax/movie/filter/').get_data(as_text=True)
    assert '<script>alert(1)</script>' not in html and '&lt;script&gt;' in html
