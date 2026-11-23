"""Error pages: crashes, expired forms and wrong methods."""
from rateflix.models import Genre


def test_a_crash_shows_the_error_page_and_saves_nothing(client, app, monkeypatch):
    ## in testing, Flask normally raises errors straight into the test; turn that off to see the real page
    monkeypatch.setitem(app.config, 'PROPAGATE_EXCEPTIONS', False)
    response = client.get('/_test/crash/')
    assert response.status_code == 500
    assert b'Something went wrong' in response.data
    assert Genre.query.filter_by(genre_name='Saved by a request that crashed').count() == 0
    ## and the app keeps working afterwards
    assert client.get('/').status_code == 200


def test_a_form_without_its_token_gets_the_expired_form_page(client, app, monkeypatch):
    monkeypatch.setitem(app.config, 'WTF_CSRF_ENABLED', True)
    response = client.post('/user/login/', data={'email': 'a@test.com', 'password': 'x'})
    assert response.status_code == 400
    assert b'This form has expired' in response.data and b'Reason:' in response.data


def test_wrong_method_gets_a_friendly_page(client):
    response = client.get('/confirm/delete/genre/1/')
    assert response.status_code == 405
    assert b'does not work on its own' in response.data
