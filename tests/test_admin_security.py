"""Admin pages and actions: only a logged-in admin can use them, deletes need a POST,
and unknown ids give a 404 page instead of a crash."""
import pytest

from conftest import AJAX, IDS, log_in_admin, log_in_member
from rateflix.models import Actor, Genre, Movie, MovieActor, MovieGenre, Producer, Studio, db

## every admin page that can be opened in the browser (filled in with real ids per test)
ADMIN_PAGES = [
    '/admin/', '/admin/movies/', '/admin/addmovie/', '/admin/movie/update/{cartoon}/',
    '/admin/movie/genre/{cartoon}/', '/admin/addgenre/{cartoon}/', '/admin/movie/actors/{cartoon}/',
    '/admin/addactor/{cartoon}/', '/admin/delgenre/{cartoon}/{animation}', '/admin/delactor/{cartoon}/{actor_one}',
    '/admin/actors/', '/admin/actors/add/', '/admin/actors/update/{actor_one}/', '/admin/actors/delete/{actor_one}/',
    '/admin/producers/', '/admin/producers/add/', '/admin/producers/update/{producer}/', '/admin/delete/producer/{producer}/',
    '/admin/genres/', '/admin/genre/add/', '/admin/delete/genre/{drama}/',
    '/admin/studios/', '/admin/studio/add/', '/admin/update/studio/{studio}/', '/admin/delete/studio/{studio}/',
]

## the final delete actions, and how to check that the row is gone
DELETES = [
    ('/confirm/delete/actor/{actor_two}', lambda: db.session.get(Actor, IDS['actor_two'])),
    ('/confirm/delete/producer/{producer}/', lambda: db.session.get(Producer, IDS['producer'])),
    ('/confirm/delete/genre/{drama}/', lambda: db.session.get(Genre, IDS['drama'])),
    ('/confirm/delete/studio/{other_studio}/', lambda: db.session.get(Studio, IDS['other_studio'])),
    ('/admin/delgenre/confirm/{cartoon}/{comedy}/',
     lambda: MovieGenre.query.filter_by(movie_id=IDS['cartoon'], genre_id=IDS['comedy']).first()),
    ('/admin/delactor/confirm/{cartoon}/{actor_one}',
     lambda: MovieActor.query.filter_by(movie_id=IDS['cartoon'], actor_id=IDS['actor_one']).first()),
]


@pytest.mark.parametrize('page', ADMIN_PAGES)
def test_admin_pages_send_visitors_to_the_admin_login(client, page):
    response = client.get(page.format(**IDS))
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/login/')


@pytest.mark.parametrize('page', ADMIN_PAGES)
def test_admin_pages_send_members_to_the_admin_login(client, page):
    log_in_member(client)
    response = client.get(page.format(**IDS))
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/login/')


@pytest.mark.parametrize('page', ADMIN_PAGES)
def test_admin_pages_open_for_an_admin(client, page):
    log_in_admin(client)
    assert client.get(page.format(**IDS)).status_code == 200


@pytest.mark.parametrize('url, row', DELETES)
def test_visiting_a_delete_address_deletes_nothing(client, url, row):
    log_in_admin(client)
    response = client.get(url.format(**IDS))
    assert response.status_code == 405
    assert row() is not None


@pytest.mark.parametrize('url, row', DELETES)
def test_visitors_cannot_delete(client, url, row):
    response = client.post(url.format(**IDS))
    assert response.status_code == 302 and response.headers['Location'].endswith('/admin/login/')
    assert row() is not None


@pytest.mark.parametrize('url, row', DELETES)
def test_members_cannot_delete(client, url, row):
    log_in_member(client)
    client.post(url.format(**IDS))
    assert row() is not None


@pytest.mark.parametrize('url, row', DELETES)
def test_admins_can_delete(client, url, row):
    log_in_admin(client)
    response = client.post(url.format(**IDS))
    assert response.status_code == 302
    assert row() is None


def test_deleting_an_actor_in_a_cast_leaves_no_broken_cast_rows(client):
    log_in_admin(client)
    client.post('/confirm/delete/actor/{actor_one}'.format(**IDS))
    assert MovieActor.query.filter((MovieActor.actor_id == None) | (MovieActor.actor_id == IDS['actor_one'])).count() == 0  # noqa: E711
    assert client.get('/movie/info/{cartoon}'.format(**IDS)).status_code == 200


def test_deleting_a_genre_in_use_leaves_no_empty_tags(client):
    log_in_admin(client)
    client.post('/confirm/delete/genre/{animation}/'.format(**IDS))
    assert MovieGenre.query.filter((MovieGenre.genre_id == None) | (MovieGenre.genre_id == IDS['animation'])).count() == 0  # noqa: E711


@pytest.mark.parametrize('who', ['visitor', 'member'])
def test_only_admins_can_change_a_movie_status(client, who):
    if who == 'member':
        log_in_member(client)
    response = client.post('/admin/update_movie_status/', headers=AJAX,
                           data={'movieid': IDS['cartoon'], 'status': 'pending'})
    assert response.status_code == 401
    assert db.session.get(Movie, IDS['cartoon']).movie_status == 'approved'


def test_admin_can_approve_a_movie(client):
    log_in_admin(client)
    response = client.post('/admin/update_movie_status/', headers=AJAX,
                           data={'movieid': IDS['alice_pending'], 'status': 'approved'})
    assert response.status_code == 204
    assert db.session.get(Movie, IDS['alice_pending']).movie_status == 'approved'


def test_unknown_status_values_are_refused(client):
    log_in_admin(client)
    response = client.post('/admin/update_movie_status/', headers=AJAX,
                           data={'movieid': IDS['cartoon'], 'status': 'deleted'})
    assert response.status_code == 400
    assert db.session.get(Movie, IDS['cartoon']).movie_status == 'approved'


@pytest.mark.parametrize('page', [
    '/admin/movie/update/999/', '/admin/movie/genre/999/', '/admin/addgenre/999/', '/admin/movie/actors/999/',
    '/admin/addactor/999/', '/admin/delgenre/{cartoon}/999', '/admin/delactor/{cartoon}/999',
    '/admin/actors/update/999/', '/admin/actors/delete/999/', '/admin/producers/update/999/',
    '/admin/delete/producer/999/', '/admin/delete/genre/999/', '/admin/update/studio/999/', '/admin/delete/studio/999/',
])
def test_unknown_ids_give_a_404_page(client, page):
    log_in_admin(client)
    response = client.get(page.format(**IDS))
    assert response.status_code == 404
    assert b'Page not found' in response.data


def test_plain_text_admin_password_is_replaced_by_a_hash_on_first_login(client):
    from rateflix.models import Admin
    admin = db.session.get(Admin, IDS['admin'])
    admin.admin_password = 'typed-into-the-database'
    db.session.commit()

    response = client.post('/admin/login/', data={'email': 'admin@test.com', 'password': 'typed-into-the-database'})
    assert response.status_code == 302
    assert db.session.get(Admin, IDS['admin']).admin_password.startswith(('scrypt:', 'pbkdf2:'))


def test_wrong_admin_password_is_refused(client):
    response = client.post('/admin/login/', data={'email': 'admin@test.com', 'password': 'wrong'})
    assert response.status_code == 200
    assert b'Incorrect password' in response.data
    assert client.get('/admin/').status_code == 302
