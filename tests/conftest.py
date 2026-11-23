"""Shared setup for the RateFlix tests.

The tests use a throwaway SQLite database and upload folder in a temporary directory,
never your MySQL database. Run them from the project folder:

    pip install -r requirements-dev.txt
    pytest
"""
import os
import tempfile
from datetime import date
from pathlib import Path

import pytest

## these must be set before the app is imported, because the app is created on import
_tmp = Path(tempfile.mkdtemp(prefix='rateflix-tests-'))
os.environ['DATABASE_URL'] = 'sqlite:///' + (_tmp / 'test.db').as_posix()
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['UPLOAD_FOLDER'] = str(_tmp / 'uploads')
os.environ.pop('MYSQL_URL', None)

from werkzeug.security import generate_password_hash  # noqa: E402

from rateflix import app as flask_app  # noqa: E402
from rateflix.models import (Actor, Admin, Genre, Member, Movie, MovieActor,  # noqa: E402
                             MovieGenre, Producer, Rating, Review, Studio, db)

## safety net: never run the tests against a real database
assert flask_app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'), 'Tests must use SQLite'

## the form token check is switched off for most tests; test_errors switches it back on
flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)


## a page that saves something and then crashes, to test the error page and the rollback.
## Routes must be added before the first request, so it lives here.
@flask_app.route('/_test/crash/')
def _test_crash():
    db.session.add(Genre(genre_name='Saved by a request that crashed'))
    db.session.flush()
    raise RuntimeError('deliberate test crash')


ADMIN = {'email': 'admin@test.com', 'password': 'admin-pass-1'}
ALICE = {'email': 'alice@test.com', 'password': 'alice-pass-1'}
BOB = {'email': 'bob@test.com', 'password': 'bob-pass-1'}

## ids of the rows created by seed(), filled in for each test
IDS = {}


def seed():
    """A small, known set of rows: 1 admin, 2 members, 4 movies (3 live, 1 pending)."""
    admin = Admin(admin_firstname='Ada', admin_lastname='Admin', admin_username='admin',
                  admin_email=ADMIN['email'], admin_password=generate_password_hash(ADMIN['password']))
    alice = Member(member_firstname='Alice', member_lastname='A', member_username='alice',
                   member_email=ALICE['email'], member_password=generate_password_hash(ALICE['password']))
    bob = Member(member_firstname='Bob', member_lastname='B', member_username='bob',
                 member_email=BOB['email'], member_password=generate_password_hash(BOB['password']))
    studio = Studio(studio_name='Test Studio')
    other_studio = Studio(studio_name='Other Studio')
    producer = Producer(producer_name='Test Producer')
    animation, drama, comedy = Genre(genre_name='Animation'), Genre(genre_name='Drama'), Genre(genre_name='Comedy')
    actor_one, actor_two = Actor(actor_name='Actor One'), Actor(actor_name='Actor Two')
    db.session.add_all([admin, alice, bob, studio, other_studio, producer, animation, drama, comedy, actor_one, actor_two])
    db.session.flush()

    cartoon = Movie(movie_title='Inside Out 2', movie_release_date=date(2024, 6, 14), movie_status='approved',
                    production_studio=studio.studio_id, producer_id=producer.producer_id)
    drama_movie = Movie(movie_title='Quiet Drama', movie_release_date=date(2023, 3, 1), movie_status='approved',
                        production_studio=other_studio.studio_id)
    alice_live = Movie(movie_title='Alice Live Movie', movie_release_date=date(2022, 1, 1), movie_status='approved',
                       production_studio=studio.studio_id, added_by=alice.member_id)
    alice_pending = Movie(movie_title='Alice Pending Movie', movie_release_date=date(2025, 1, 1), movie_status='pending',
                          production_studio=studio.studio_id, added_by=alice.member_id)
    db.session.add_all([cartoon, drama_movie, alice_live, alice_pending])
    db.session.flush()

    db.session.add_all([
        MovieGenre(movie_id=cartoon.movie_id, genre_id=animation.genre_id),
        MovieGenre(movie_id=cartoon.movie_id, genre_id=comedy.genre_id),
        MovieGenre(movie_id=drama_movie.movie_id, genre_id=drama.genre_id),
        MovieActor(movie_id=cartoon.movie_id, actor_id=actor_one.actor_id),
    ])
    db.session.commit()

    IDS.clear()
    IDS.update(admin=admin.admin_id, alice=alice.member_id, bob=bob.member_id,
               studio=studio.studio_id, other_studio=other_studio.studio_id, producer=producer.producer_id,
               animation=animation.genre_id, drama=drama.genre_id, comedy=comedy.genre_id,
               actor_one=actor_one.actor_id, actor_two=actor_two.actor_id,
               cartoon=cartoon.movie_id, drama_movie=drama_movie.movie_id,
               alice_live=alice_live.movie_id, alice_pending=alice_pending.movie_id)


@pytest.fixture
def app():
    """A fresh database with the seed rows for every test."""
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        seed()
        yield flask_app
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


def log_in_member(client, who=ALICE):
    return client.post('/user/login/', data={'email': who['email'], 'password': who['password']})


def log_in_admin(client):
    return client.post('/admin/login/', data={'email': ADMIN['email'], 'password': ADMIN['password']})


## background requests from the pages send this header (jQuery adds it)
AJAX = {'X-Requested-With': 'XMLHttpRequest'}
