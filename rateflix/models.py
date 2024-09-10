from datetime import datetime 
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Member(db.Model):
    member_id = db.Column(db.Integer, primary_key=True)
    member_firstname = db.Column(db.String(255), nullable=False)
    member_lastname = db.Column(db.String(255), nullable=False)
    member_username = db.Column(db.String(255), unique=True, nullable=False)
    member_email = db.Column(db.String(255), unique=True, nullable=False)
    member_password = db.Column(db.String(255), nullable=False)
    member_join_date = db.Column(db.DateTime, default=datetime.utcnow)
    member_profile_pic = db.Column(db.String(255))
    member_bio = db.Column(db.Text)
    member_date_of_birth = db.Column(db.Date)

    ratings = db.relationship('Rating', back_populates='member')
    reviews = db.relationship('Review', back_populates='member')
    comments = db.relationship('Comment', back_populates='member')
    watchlists = db.relationship('Watchlist', back_populates='member')
    sent_requests = db.relationship('Friendship', foreign_keys='Friendship.request_by', back_populates='requester')
    received_requests = db.relationship('Friendship', foreign_keys='Friendship.request_to', back_populates='receiver')
    notifications = db.relationship('Notification', back_populates='receiver')
    comment_likes = db.relationship('CommentLike', back_populates='member')
    movies = db.relationship('Movie', back_populates='added_by_member')
    


class Producer(db.Model):
    producer_id = db.Column(db.Integer, primary_key=True)
    producer_name = db.Column(db.String(255), nullable=False)

    movies = db.relationship('Movie', back_populates='producer')


class Movie(db.Model):
    movie_id = db.Column(db.Integer, primary_key=True)
    movie_title = db.Column(db.String(255), nullable=False)
    producer_id = db.Column(db.Integer, db.ForeignKey('producer.producer_id'))
    movie_release_date = db.Column(db.Date)
    movie_description = db.Column(db.Text)
    movie_poster = db.Column(db.String(255))
    movie_trailer = db.Column(db.String(255))
    movie_status = db.Column(db.Enum('pending', 'approved'), nullable=False, default='pending')
    production_studio = db.Column(db.Integer, db.ForeignKey('studio.studio_id'))
    added_by = db.Column(db.Integer, db.ForeignKey('member.member_id'))

    producer = db.relationship('Producer', back_populates='movies')
    genres = db.relationship('MovieGenre', back_populates='movie')
    ratings = db.relationship('Rating', back_populates='movie')
    reviews = db.relationship('Review', back_populates='movie')
    watchlist_movies = db.relationship('WatchlistMovie', back_populates='movie')
    movie_actors = db.relationship('MovieActor', back_populates='movie')
    studio = db.relationship('Studio', back_populates='movie')
    added_by_member = db.relationship('Member', back_populates='movies')


class Genre(db.Model):
    genre_id = db.Column(db.Integer, primary_key=True)
    genre_name = db.Column(db.String(255), nullable=False)

    movies = db.relationship('MovieGenre', back_populates='genre')


class MovieGenre(db.Model):
    movie_genre_id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.movie_id', ondelete='CASCADE'))
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.genre_id', ondelete='CASCADE'))

    movie = db.relationship('Movie', back_populates='genres')
    genre = db.relationship('Genre', back_populates='movies')


class Rating(db.Model):
    rating_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id', ondelete='CASCADE'))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.movie_id', ondelete='CASCADE'))
    rating_score = db.Column(db.Integer, nullable=False)  # Rating score between 1 and 5
    rating_date = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', back_populates='ratings')
    movie = db.relationship('Movie', back_populates='ratings')


class Review(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id', ondelete='CASCADE'))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.movie_id', ondelete='CASCADE'))
    review_content = db.Column(db.Text)
    review_date = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', back_populates='reviews')
    movie = db.relationship('Movie', back_populates='reviews')
    comments = db.relationship('Comment', back_populates='review')


class Comment(db.Model):
    comment_id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.review_id', ondelete='CASCADE'))
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id', ondelete='CASCADE'))
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comment.comment_id', ondelete='CASCADE'), nullable=True)
    comment_content = db.Column(db.Text)
    comment_date = db.Column(db.DateTime, default=datetime.utcnow)

    review = db.relationship('Review', back_populates='comments')
    member = db.relationship('Member', back_populates='comments')
    parent = db.relationship('Comment', remote_side=[comment_id], back_populates='replies')
    replies = db.relationship('Comment', back_populates='parent')
    likes = db.relationship('CommentLike', back_populates='comment')


class CommentLike(db.Model):
    comment_like_id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.comment_id', ondelete='CASCADE'))
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id', ondelete='CASCADE'))
    like_dislike = db.Column(db.Integer, nullable=False)

    comment = db.relationship('Comment', back_populates='likes')
    member = db.relationship('Member', back_populates='comment_likes')


class Watchlist(db.Model):
    watchlist_id = db.Column(db.Integer, primary_key=True)
    watchlist_name = db.Column(db.String(255), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id', ondelete='CASCADE'))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    privacy = db.Column(db.Enum('public', 'private', name='privacy_enum'), nullable=False, default='public')

    member = db.relationship('Member', back_populates='watchlists')
    movies = db.relationship('WatchlistMovie', back_populates='watchlist')


class WatchlistMovie(db.Model):
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlist.watchlist_id', ondelete='CASCADE'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.movie_id', ondelete='CASCADE'), primary_key=True)

    watchlist = db.relationship('Watchlist', back_populates='movies')
    movie = db.relationship('Movie', back_populates='watchlist_movies')


class Friendship(db.Model):
    friendship_id = db.Column(db.Integer, primary_key=True)
    request_by = db.Column(db.Integer, db.ForeignKey('member.member_id', ondelete='CASCADE'))
    request_to = db.Column(db.Integer, db.ForeignKey('member.member_id', ondelete='CASCADE'))
    friendship_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('approved', 'pending', 'rejected', name='friendship_status_enum'), nullable=False, default='pending')

    requester = db.relationship('Member', foreign_keys=[request_by], back_populates='sent_requests')
    receiver = db.relationship('Member', foreign_keys=[request_to], back_populates='received_requests')


class Notification(db.Model):
    notification_id = db.Column(db.Integer, primary_key=True)
    receiver_id = db.Column('receiver', db.Integer, db.ForeignKey('member.member_id', ondelete='CASCADE'))
    notification_content = db.Column(db.Text)
    notification_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    receiver = db.relationship('Member', back_populates='notifications')


class Actor(db.Model):
    actor_id = db.Column(db.Integer, primary_key=True)
    actor_name = db.Column(db.String(255), nullable=False)
    actor_bio = db.Column(db.Text)
    actor_birthdate = db.Column(db.Date)
    actor_photo = db.Column(db.String(255))

    movie_actors = db.relationship('MovieActor', back_populates='actor')


class MovieActor(db.Model):
    movie_actor_id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.movie_id', ondelete='CASCADE'))
    actor_id = db.Column(db.Integer, db.ForeignKey('actor.actor_id', ondelete='CASCADE'))
    role_name = db.Column(db.String(255))

    movie = db.relationship('Movie', back_populates='movie_actors')
    actor = db.relationship('Actor', back_populates='movie_actors')


class Admin(db.Model):
    admin_id = db.Column(db.Integer, primary_key=True)
    admin_firstname = db.Column(db.String(255), nullable=False)
    admin_lastname = db.Column(db.String(255), nullable=False)
    admin_username = db.Column(db.String(255), unique=True, nullable=False)
    admin_email = db.Column(db.String(255), unique=True, nullable=False)
    admin_password = db.Column(db.String(255), nullable=False)
    admin_lastloggedin = db.Column(db.DateTime)

class Studio(db.Model):
    studio_id = db.Column(db.Integer, primary_key=True)
    studio_name = db.Column(db.String(255), nullable=False)

    movie = db.relationship('Movie', back_populates='studio')

    # movies = db.relationship('MovieGenre', back_populates='genre')