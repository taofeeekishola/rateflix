from flask import render_template,redirect,flash,request,session

from rateflix import app
from rateflix.models import db,Member,Studio,Producer,Genre,Actor,Movie,MovieActor,MovieGenre,Review

@app.route('/admin/')
def admin():
    return render_template('admin/admin.html')

@app.route('/admin/movies/')
def admin_movies():
    movies = db.session.query(Movie).all()
    movie_genre = db.session.query(MovieGenre).all()
    return render_template('admin/movies.html', movies=movies, movie_genre=movie_genre)