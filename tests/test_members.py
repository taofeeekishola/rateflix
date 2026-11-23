"""Member accounts, member movies, reviews and ratings."""
from conftest import ALICE, BOB, IDS, log_in_member
from rateflix.models import Member, Movie, MovieActor, Rating, Review, db


def sign_up(client, username='newbie', email='newbie@test.com'):
    return client.post('/user/signup/', data={
        'first_name': 'New', 'last_name': 'Member', 'user_name': username, 'email': email,
        'password': 'pass-1234', 'con_password': 'pass-1234'})


def test_sign_up_creates_the_account_and_logs_in(client):
    response = sign_up(client)
    assert response.status_code == 302
    assert Member.query.filter_by(member_username='newbie').count() == 1
    assert client.get('/user/profile/').status_code == 200


def test_sign_up_with_a_taken_username_says_so(client):
    response = sign_up(client, username='alice', email='someone@test.com')
    assert response.status_code == 200
    assert b'That username is already taken' in response.data
    assert Member.query.count() == 2


def test_sign_up_with_a_taken_email_says_so(client):
    response = sign_up(client, username='someone', email=ALICE['email'])
    assert b'already uses that email' in response.data
    assert Member.query.count() == 2


def test_wrong_password_is_refused(client):
    response = client.post('/user/login/', data={'email': ALICE['email'], 'password': 'nope'})
    assert b'Incorrect password' in response.data
    assert client.get('/user/profile/').status_code == 302


def test_member_can_edit_their_own_pending_movie(client):
    log_in_member(client)
    assert client.get('/user/movie/update/{alice_pending}/'.format(**IDS)).status_code == 200


def test_member_cannot_edit_their_movie_once_it_is_live(client):
    log_in_member(client)
    assert client.get('/user/movie/update/{alice_live}/'.format(**IDS)).status_code == 404


def test_member_cannot_edit_someone_elses_movie(client):
    log_in_member(client, BOB)
    url = '/user/movie/update/{alice_pending}/'.format(**IDS)
    assert client.get(url).status_code == 404
    response = client.post(url, data={'title': 'Changed by Bob', 'release_date': '2025-01-01', 'studio': IDS['studio']})
    assert response.status_code == 404
    assert db.session.get(Movie, IDS['alice_pending']).movie_title == 'Alice Pending Movie'


def test_editing_adds_exactly_the_chosen_actor(client):
    log_in_member(client)
    client.post('/user/movie/update/{alice_pending}/'.format(**IDS), data={
        'title': 'Alice Pending Movie', 'release_date': '2025-01-01', 'studio': IDS['studio'],
        'producer': '', 'actor': IDS['actor_two']})
    cast = [ma.actor_id for ma in MovieActor.query.filter_by(movie_id=IDS['alice_pending'])]
    assert cast == [IDS['actor_two']]


def test_member_can_add_a_movie_with_no_producer_or_actor(client):
    log_in_member(client)
    response = client.post('/user/add_movie/', data={
        'title': 'Brand New Movie', 'release_date': '2025-05-05', 'studio': IDS['studio'],
        'producer': '', 'actor': '', 'genre': [IDS['drama'], IDS['comedy']]})
    assert response.status_code in (200, 302)
    movie = Movie.query.filter_by(movie_title='Brand New Movie').one()
    assert movie.movie_status == 'pending' and movie.producer_id is None and movie.added_by == IDS['alice']
    assert len(movie.genres) == 2


def test_missing_movie_fields_are_explained(client):
    log_in_member(client)
    response = client.post('/user/add_movie/', data={'title': '', 'release_date': '', 'studio': ''})
    for message in (b'Enter the title of the movie', b'Pick the release date', b'Choose a studio'):
        assert message in response.data


def test_profile_saves_without_a_date_of_birth(client):
    log_in_member(client)
    client.post('/user/update/profile/', data={'first_name': 'Alice', 'last_name': 'A', 'bio': 'Loves cartoons', 'date_of_birth': ''})
    assert db.session.get(Member, IDS['alice']).member_bio == 'Loves cartoons'


def post_review(client, text, movie='cartoon'):
    return client.post('/ajax/movie/review/', data={'reviewData': text, 'movieId': IDS[movie]})


def test_reviews_need_a_login_and_some_text(client):
    assert post_review(client, 'Great').status_code == 401
    log_in_member(client)
    assert post_review(client, '   ').status_code == 400


def test_the_same_review_twice_is_saved_once(client):
    log_in_member(client)
    first = post_review(client, 'Loved it').get_json()
    second = post_review(client, 'Loved it').get_json()
    assert second['duplicate'] and second['review_id'] == first['review_id']
    assert Review.query.count() == 1


def test_only_the_author_or_an_admin_can_delete_a_review(client):
    log_in_member(client)
    review_id = post_review(client, 'Mine').get_json()['review_id']

    other = client.application.test_client()
    log_in_member(other, BOB)
    assert other.post(f'/ajax/movie/review/{review_id}/delete/').status_code == 403
    assert db.session.get(Review, review_id) is not None

    assert client.post(f'/ajax/movie/review/{review_id}/delete/').status_code == 200
    assert db.session.get(Review, review_id) is None


def test_admin_can_delete_any_review(client):
    log_in_member(client)
    review_id = post_review(client, 'Delete me').get_json()['review_id']
    admin = client.application.test_client()
    admin.post('/admin/login/', data={'email': 'admin@test.com', 'password': 'admin-pass-1'})
    assert admin.post(f'/ajax/movie/review/{review_id}/delete/').status_code == 200


def rate(client, score):
    return client.post('/user/submitrating/', data={'rating': score, 'movieId': IDS['cartoon']})


def test_ratings_average_and_can_be_changed(client):
    assert rate(client, 4).status_code == 401
    log_in_member(client)
    assert rate(client, 4).get_json() == {'your_rating': 4, 'average_rating': 4.0, 'rating_count': 1}

    bob = client.application.test_client()
    log_in_member(bob, BOB)
    assert rate(bob, 3).get_json()['average_rating'] == 3.5

    changed = rate(client, 5).get_json()
    assert changed['average_rating'] == 4.0 and changed['rating_count'] == 2
    assert Rating.query.count() == 2


def test_out_of_range_ratings_are_refused(client):
    log_in_member(client)
    assert rate(client, 6).status_code == 400
    assert rate(client, 0).status_code == 400
