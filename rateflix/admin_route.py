import os,secrets,hmac
from functools import wraps
from flask import render_template,redirect,flash,request,session,url_for, jsonify, make_response, g, abort
from werkzeug.security import generate_password_hash,check_password_hash

from rateflix import app, upload_path
from rateflix.forms import Login,MovieForm,ActorDetail,ProducerDetail,GenreDetail,StudioDetail
from rateflix.models import db,Member,Studio,Producer,Genre,Actor,Movie,MovieActor,MovieGenre,Admin,Review,Rating


## the admin who is logged in, or None
def current_admin():
    admin_id = session.get('admin_id')
    return db.session.get(Admin, admin_id) if admin_id is not None else None

## put @admin_required under @app.route on every admin page and action.
## Anyone not logged in as an admin is sent to the admin login page (background requests get a 401 instead),
## so no admin page or action can run without a login. The admin is available as g.admin_session
## and in every template as admin_session.
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        admin = current_admin()
        if admin is None:
            session.pop('admin_id', None)   # e.g. the admin account was deleted
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Your admin session has ended. Log in again.'}), 401
            flash('You need to be logged in as an admin')
            return redirect('/admin/login/')
        g.admin_session = admin
        return view(*args, **kwargs)
    return wrapped

## checks an admin's password.
## Passwords should be stored as werkzeug hashes. An admin inserted manually with a plain-text
## password can still log in once, and that password is then replaced with a hash.
def admin_password_matches(admin, password):
    stored = admin.admin_password or ''
    if stored.startswith(('scrypt:', 'pbkdf2:')):
        return check_password_hash(stored, password)

    if hmac.compare_digest(stored.encode(), password.encode()):
        admin.admin_password = generate_password_hash(password)
        db.session.commit()
        return True
    return False

## saves an uploaded file under a random name and returns that name
def save_upload(file, subfolder):
    extension = os.path.splitext(file.filename)[-1]
    name = secrets.token_hex(10) + extension
    file.save(upload_path(subfolder, name))
    return name

## this is the route that displays the user details
@app.route('/admin/')
@admin_required
def admin():
    user = Member.query.order_by(Member.member_join_date.desc()).all()

    ## numbers for the dashboard
    stats = {
        'members': len(user),
        'approved': Movie.query.filter(Movie.movie_status == 'approved').count(),
        'pending': Movie.query.filter(Movie.movie_status == 'pending').count(),
        'reviews': Review.query.count(),
        'ratings': Rating.query.count(),
    }
    pending_movies = Movie.query.filter(Movie.movie_status == 'pending').order_by(Movie.movie_id.desc()).limit(5).all()

    return render_template('admin/admin.html', user=user, stats=stats, pending_movies=pending_movies)

##route to allow the admin login
@app.route('/admin/login/', methods=['GET','POST'])
def admin_login():
    if current_admin() is not None:
        return redirect('/admin/')

    login = Login()

    if login.validate_on_submit():
        email = request.form.get('email')
        password = request.form.get('password')

        data = db.session.query(Admin).filter(Admin.admin_email == email).first()
        if data and admin_password_matches(data, password):
            session['admin_id'] = data.admin_id
            app.logger.info('Admin %s logged in', email)
            return redirect('/admin/')

        app.logger.warning('Failed admin login for %s from %s', email, request.remote_addr)
        flash('Incorrect password.' if data else 'No admin account uses that email.')

    return render_template('admin/admin_login.html', login=login)

## route to logout
@app.route('/admin/logout/')
def admin_logout():
    session.pop('admin_id', None)
    flash('You are now logged out')
    return redirect('/admin/login/')

#route to show movie details
@app.route('/admin/movies/')
@admin_required
def admin_movies():
    ## movies waiting for approval first, then the newest
    movies = db.session.query(Movie).order_by(Movie.movie_status.asc(), Movie.movie_id.desc()).all()
    return render_template('admin/all_movies.html', movies=movies)

##route for admin to add a movie
@app.route('/admin/addmovie/',methods=['GET','POST'])
@admin_required
def admin_add_movie():
    actor = Actor.query.all()
    producer = Producer.query.all()
    studio =Studio.query.all()
    genre = Genre.query.all()
    movieform = MovieForm()

    if movieform.validate_on_submit():
        poster = request.files.get('poster')
        trailer = request.files.get('trailer')
        movie_actor = request.form.get('actor')

        movie_details = Movie(movie_title=request.form.get('title'),
                              producer_id=request.form.get('producer') or None,   # "Not listed"
                              movie_release_date=movieform.release_date.data,
                              movie_description=request.form.get('description'),
                              production_studio=request.form.get('studio'),
                              movie_poster=save_upload(poster, 'poster') if poster and poster.filename else None,
                              movie_trailer=save_upload(trailer, 'trailers') if trailer and trailer.filename else None)
        db.session.add(movie_details)
        db.session.flush()   # gives the movie its id

        if movie_actor:
            db.session.add(MovieActor(movie_id=movie_details.movie_id, actor_id=int(movie_actor)))
        for g_id in request.form.getlist('genre'):
            db.session.add(MovieGenre(movie_id=movie_details.movie_id, genre_id=int(g_id)))

        db.session.commit()
        app.logger.info('Admin %s added movie %s', g.admin_session.admin_email, movie_details.movie_title)
        flash('Movie has been succesfully added')
        return redirect('/admin/movies/')

    return render_template('admin/admin_add_movie.html', movieform=movieform,actor=actor,producer=producer,studio=studio,genre=genre)

##admin can update the values of a movie in this route
@app.route('/admin/movie/update/<int:id>/', methods=['GET','POST'])
@admin_required
def update_movies(id):
    movie = db.get_or_404(Movie, id)
    actors = db.session.query(Actor).all()
    producers = db.session.query(Producer).all()
    studio = db.session.query(Studio).all()
    genre = db.session.query(Genre).all()

    movieform = MovieForm()

    if movieform.validate_on_submit():
        poster = request.files.get('poster')
        trailer = request.files.get('trailer')
        if poster and poster.filename:
            movie.movie_poster = save_upload(poster, 'poster')
        if trailer and trailer.filename:
            movie.movie_trailer = save_upload(trailer, 'trailers')

        ##updating data in the database
        movie.movie_title = request.form.get('title')
        movie.movie_release_date = movieform.release_date.data
        movie.movie_description = request.form.get('description')
        movie.production_studio = request.form.get('studio')
        movie.producer_id = request.form.get('producer') or None   # "Not listed"

        ## add any new cast member and genres (ones already on the movie are skipped)
        existing_actor_ids = {ma.actor_id for ma in MovieActor.query.filter_by(movie_id=id)}
        for actor_id in [int(a) for a in request.form.getlist('actor') if a]:   # empty means "no change"
            if actor_id not in existing_actor_ids:
                db.session.add(MovieActor(movie_id=id, actor_id=actor_id))

        existing_genre_ids = {mg.genre_id for mg in MovieGenre.query.filter_by(movie_id=id)}
        for genre_id in [int(x) for x in request.form.getlist('genre')]:
            if genre_id not in existing_genre_ids:
                db.session.add(MovieGenre(movie_id=id, genre_id=genre_id))

        db.session.commit()
        flash('Movie has been updated')
        return redirect('/admin/movies/')

    return render_template('admin/update_movie.html', movie=movie, movieform=movieform, all_actors=actors, producers=producers,studio=studio, genre=genre)

##route to see the genres of a movie
@app.route('/admin/movie/genre/<int:id>/')
@admin_required
def movie_genres(id):
    movie = db.get_or_404(Movie, id)
    genres = MovieGenre.query.filter(MovieGenre.movie_id == id).all()
    return render_template('admin/view_movie_genres.html',movie=movie,genres=genres)

## route to add a new genre to a movie
@app.route('/admin/addgenre/<int:id>/', methods=['GET','POST'])
@admin_required
def admin_addgenre(id):
    movie = db.get_or_404(Movie, id)
    genres = Genre.query.all()

    ##list to get all the ids of the current movie
    movie_genre_ids = [mg.genre_id for mg in MovieGenre.query.filter(MovieGenre.movie_id == id).all()]

    if request.method == "POST":
        for g_id in request.form.getlist('genre'):
            if int(g_id) not in movie_genre_ids:
                db.session.add(MovieGenre(movie_id=id, genre_id=int(g_id)))
        db.session.commit()

        flash('Genre has been added')
        return redirect(url_for('movie_genres', id=id))

    return render_template('admin/add_moviegenre.html', movie=movie, genres=genres,movie_genre_ids=movie_genre_ids)

##route to delete a genre from a movie
@app.route('/admin/delgenre/<int:id>/<int:id2>')
@admin_required
def admin_delgenre(id,id2):
    movie = db.get_or_404(Movie, id)
    genre = MovieGenre.query.filter(MovieGenre.movie_id == id,MovieGenre.genre_id==id2).first_or_404()
    return render_template('admin/del_movie_genre.html',movie=movie,genre=genre)

##confirm genre deletion
@app.route('/admin/delgenre/confirm/<int:id>/<int:id2>/', methods=['POST'])
@admin_required
def admin_confirm_delgenre(id,id2):
    genre = MovieGenre.query.filter(MovieGenre.movie_id == id,MovieGenre.genre_id==id2).first_or_404()
    db.session.delete(genre)
    db.session.commit()

    flash('Genre has been deleted')
    return redirect(url_for('movie_genres', id=id))

##route to see all the actors of a movie
@app.route('/admin/movie/actors/<int:id>/')
@admin_required
def movie_actors(id):
    movie = db.get_or_404(Movie, id)
    actors = MovieActor.query.filter(MovieActor.movie_id == id).all()
    return render_template('admin/view_movie_actors.html',movie=movie,actors=actors)

## route to add a new actor to a movie
@app.route('/admin/addactor/<int:id>/',methods=['GET','POST'])
@admin_required
def admin_addactor(id):
    movie = db.get_or_404(Movie, id)
    actors = db.session.query(Actor).all()

    if request.method == 'POST':
        actor = db.get_or_404(Actor, request.form.get('actor', type=int) or 0)
        if not MovieActor.query.filter_by(movie_id=id, actor_id=actor.actor_id).first():
            db.session.add(MovieActor(movie_id=id, actor_id=actor.actor_id))
            db.session.commit()

        flash('Actor has been added')
        return redirect(url_for('movie_actors', id=id))

    return render_template('admin/add_movieactor.html', movie=movie, all_actors=actors)

##route to delete actor from movie
@app.route('/admin/delactor/<int:id>/<int:id2>')
@admin_required
def admin_delactor(id,id2):
    movie = db.get_or_404(Movie, id)
    actors = MovieActor.query.filter(MovieActor.actor_id == id2 , MovieActor.movie_id == id).first_or_404()
    return render_template('admin/del_movie_actor.html', actors=actors,movie=movie)

##this confirms the deletion
@app.route('/admin/delactor/confirm/<int:id>/<int:id2>', methods=['POST'])
@admin_required
def admin_confirm_delactor(id,id2):
    actors = MovieActor.query.filter(MovieActor.actor_id == id2 , MovieActor.movie_id == id).first_or_404()
    db.session.delete(actors)
    db.session.commit()

    flash('Actor has been deleted')
    return redirect(url_for('movie_actors', id=id))

## route to view all the actors in the database
@app.route('/admin/actors/')
@admin_required
def admin_actors():
    actors = Actor.query.all()
    return render_template('admin/movie_actors.html',actors=actors)

## route to add a new actor to the database
@app.route('/admin/actors/add/', methods=['GET','POST'])
@admin_required
def add_actors():
    details = ActorDetail()

    if details.validate_on_submit():
        name = request.form.get('name')
        picture = request.files.get('picture')

        ## checking if actors exists
        if Actor.query.filter(Actor.actor_name == name).first():
            flash('Actor already exists')
            return redirect('/admin/actors/')

        actor_photo = save_upload(picture, 'actors') if picture and picture.filename else 'default_actor.jpg'
        db.session.add(Actor(actor_name=name, actor_bio=request.form.get('bio'), actor_photo=actor_photo))
        db.session.commit()

        flash('Actor has been added')
        return redirect('/admin/actors/')

    return render_template('admin/add_actor.html',details=details)

## route for updating actor details
@app.route('/admin/actors/update/<int:id>/',methods=['GET','POST'])
@admin_required
def update_actor(id):
    actor = db.get_or_404(Actor, id)
    details = ActorDetail()

    if details.validate_on_submit():
        picture = request.files.get('picture')
        if picture and picture.filename:
            actor.actor_photo = save_upload(picture, 'actors')

        ## uppdating the actor details
        actor.actor_name = request.form.get('name')
        actor.actor_bio = request.form.get('bio')
        db.session.commit()

        flash('Actor has been updated')
        return redirect('/admin/actors/')

    return render_template('admin/update_actor.html',details=details, actor=actor)

##route for deleting an actor
@app.route('/admin/actors/delete/<int:id>/')
@admin_required
def delete_actor(id):
    actor = db.get_or_404(Actor, id)
    return render_template('admin/delete_actor.html',actor=actor)

##route to confirm delete (POST only, so a link or a page can't delete anything by itself)
@app.route('/confirm/delete/actor/<int:id>', methods=['POST'])
@admin_required
def confirm_actor_delete(id):
    actor = db.get_or_404(Actor, id)

    ## take them out of every cast first, otherwise those movies keep a cast entry with no actor and their pages break
    MovieActor.query.filter_by(actor_id=id).delete()
    db.session.delete(actor)
    db.session.commit()
    app.logger.info('Admin %s deleted actor %s', g.admin_session.admin_email, actor.actor_name)

    flash('Actor has been deleted')
    return redirect('/admin/actors/')


## route to see more producers
@app.route('/admin/producers/')
@admin_required
def admin_producers():
    producers = Producer.query.all()
    return render_template('admin/admin_producers.html', producers=producers)

## route for adding produce
@app.route('/admin/producers/add/', methods=['GET','POST'])
@admin_required
def add_producer():
    producer = ProducerDetail()

    if producer.validate_on_submit():
        db.session.add(Producer(producer_name=request.form.get('name')))
        db.session.commit()

        flash('Producer has been added')
        return redirect('/admin/producers/')

    return render_template('admin/add_producer.html', producer=producer)


## this is the route for updating producer details
@app.route('/admin/producers/update/<int:id>/', methods=['GET','POST'])
@admin_required
def update_producer(id):
    producerdetails = db.get_or_404(Producer, id)
    producer = ProducerDetail()

    if producer.validate_on_submit():
        producerdetails.producer_name = request.form.get('name')
        db.session.commit()

        flash('Producer has been updated')
        return redirect('/admin/producers/')

    return render_template('admin/update_producer.html',producerdetails=producerdetails,producer=producer)

##this route is for deleting a producer
@app.route('/admin/delete/producer/<int:id>/')
@admin_required
def delete_producer(id):
    producer = db.get_or_404(Producer, id)
    return render_template('admin/delete_producer.html',producer=producer)

##route for confirming the deletion of a producer
@app.route('/confirm/delete/producer/<int:id>/', methods=['POST'])
@admin_required
def confirm_delete_producer(id):
    producer = db.get_or_404(Producer, id)
    db.session.delete(producer)   # their movies keep going, with the producer shown as "Not listed"
    db.session.commit()
    app.logger.info('Admin %s deleted producer %s', g.admin_session.admin_email, producer.producer_name)

    flash('Producer has been deleted')
    return redirect('/admin/producers/')

##this route is for displaying all genres
@app.route('/admin/genres/')
@admin_required
def admin_genre():
    genres = Genre.query.all()
    return render_template('admin/admin_genre.html', genres=genres)

## this route is for adding new genres
@app.route('/admin/genre/add/', methods=['GET','POST'])
@admin_required
def add_genre():
    genre = GenreDetail()

    if genre.validate_on_submit():
        name = request.form.get('name')

        ## checking if the genre exists in the database already
        if Genre.query.filter(Genre.genre_name == name).first():
            flash('Genre already exists')
            return redirect('/admin/genres/')

        db.session.add(Genre(genre_name=name))
        db.session.commit()

        flash('Genre has been added')
        return redirect('/admin/genres/')

    return render_template('admin/add_genre.html' ,genre=genre)

## this is the route for deleting a genre
@app.route('/admin/delete/genre/<int:id>/')
@admin_required
def admin_delete_genre(id):
    genre = db.get_or_404(Genre, id)
    return render_template('admin/delete_genre.html',genre=genre)

## this routes confirms the deletion of genre
@app.route('/confirm/delete/genre/<int:id>/', methods=['POST'])
@admin_required
def confirm_delete_genre(id):
    genre = db.get_or_404(Genre, id)

    ## untag the movies first, otherwise they keep an empty genre
    MovieGenre.query.filter_by(genre_id=id).delete()
    db.session.delete(genre)
    db.session.commit()
    app.logger.info('Admin %s deleted genre %s', g.admin_session.admin_email, genre.genre_name)

    flash('Genre has been deleted')
    return redirect('/admin/genres/')

# route to change the status of a movie (called from the Movies page)
@app.route('/admin/update_movie_status/', methods=['POST'])
@admin_required
def update_movie_status():
    new_status = request.form.get('status')
    if new_status not in ('pending', 'approved'):
        return jsonify({'error': 'Status must be pending or approved.'}), 400

    movie = db.session.get(Movie, request.form.get('movieid', type=int) or 0)
    if movie is None:
        return make_response('', 404)  # Return 404 Not Found if the movie doesn't exist

    movie.movie_status = new_status
    db.session.commit()
    app.logger.info('Admin %s set %s to %s', g.admin_session.admin_email, movie.movie_title, new_status)
    return make_response('', 204)  # Return 204 No Content

## route to view all movie studio
@app.route('/admin/studios/')
@admin_required
def admin_studio():
    studio = Studio.query.all()
    return render_template('admin/admin_studio.html',studio=studio)

##route to add a new studio
@app.route('/admin/studio/add/', methods=['GET','POST'])
@admin_required
def admin_add_studio():
    studio = StudioDetail()

    if studio.validate_on_submit():
        name = request.form.get('name')

        ## checking if the studio exists in the database already
        if Studio.query.filter(Studio.studio_name == name).first():
            flash('Studio already exists')
            return redirect('/admin/studios/')

        db.session.add(Studio(studio_name=name))
        db.session.commit()

        flash('Studio has been added')
        return redirect('/admin/studios/')

    return render_template('admin/add_studio.html', studio=studio)

##route to delete a studio
@app.route('/admin/delete/studio/<int:id>/')
@admin_required
def delete_studio(id):
    studio = db.get_or_404(Studio, id)
    return render_template('admin/delete_studio.html',studio=studio)

## route to confirm deletion
@app.route('/confirm/delete/studio/<int:id>/', methods=['POST'])
@admin_required
def confirm_delete_studio(id):
    studio = db.get_or_404(Studio, id)
    db.session.delete(studio)   # its movies keep going, with the studio shown as "Not listed"
    db.session.commit()
    app.logger.info('Admin %s deleted studio %s', g.admin_session.admin_email, studio.studio_name)

    flash('Studio has been deleted')
    return redirect('/admin/studios/')

## route to update studio
@app.route('/admin/update/studio/<int:id>/',methods=['GET','POST'])
@admin_required
def update_studio(id):
    studiodetails = db.get_or_404(Studio, id)
    studio = StudioDetail()

    if studio.validate_on_submit():
        studiodetails.studio_name = request.form.get('name')
        db.session.commit()

        flash('Studio has been updated')
        return redirect('/admin/studios/')

    return render_template('admin/update_studio.html',studiodetails=studiodetails,studio=studio)
