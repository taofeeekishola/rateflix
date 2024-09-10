import os,secrets
from flask import render_template,redirect,flash,request,session,url_for

from rateflix import app
from rateflix.forms import Register,Login,MovieForm,MovieReview,ActorDetail,ProducerDetail,GenreDetail
from rateflix.models import db,Member,Studio,Producer,Genre,Actor,Movie,MovieActor,MovieGenre,Review

@app.route('/admin/')
def admin():
    return render_template('admin/admin.html')

@app.route('/admin/movies/')
def admin_movies():
    movies = db.session.query(Movie).all()
    # movie_genre = db.session.query(MovieGenre).all()
    return render_template('admin/all_movies.html', movies=movies)

##route for admin to add a movie
@app.route('/admin/addmovie/',methods=['GET','POST'])
def admin_add_movie():
    actor = Actor.query.all()
    producer = Producer.query.all()
    studio =Studio.query.all()
    genre = Genre.query.all()
    movieform = MovieForm()

    if movieform.validate_on_submit():
            title = request.form.get('title')
            release_date= request.form.get('release_date')
            summary = request.form.get('description')
            movie_actor = request.form.get('actor')
            movie_producer=request.form.get('producer')
            movie_studio = request.form.get('studio')
            movie_genre = request.form.getlist('genre')
            poster = request.files.get('poster')
            trailer = request.files.get('trailer')

            poster_name, extension1 = None, None
            trailer_name, extension2 = None, None
            
            ##checking if the poster was provided
            if poster and poster.filename:
                poster_filename = poster.filename
                poster_ext = os.path.splitext(poster_filename)
                extension1 = poster_ext[-1]
        
                ##generating new names
                poster_name = secrets.token_hex(10)
                poster.save("rateflix/static/uploads/poster/"+poster_name+extension1)
               
            
            ##checking if the trailer was provided
            if trailer and trailer.filename:
                trailer_filename = trailer.filename
                trailer_ext = os.path.splitext(trailer_filename)
                extension2 = trailer_ext[-1]

                trailer_name = secrets.token_hex(10)
                trailer.save("rateflix/static/uploads/trailers/"+trailer_name+extension2)
                

            movie_details = Movie(movie_title=title,producer_id=movie_producer,movie_release_date=release_date,movie_description=summary,production_studio=movie_studio,movie_poster=poster_name+extension1 if poster and poster.filename else None, movie_trailer=trailer_name + extension2 if trailer and trailer.filename else None )

            db.session.add(movie_details)
            db.session.commit()

            movie_id = movie_details.movie_id	

            if movie_actor:  # Ensure there is an actor ID provided
                movie_actor_data = MovieActor(movie_id=movie_id, actor_id=movie_actor)
                db.session.add(movie_actor_data)
                db.session.commit()

            if movie_genre:
                for g in movie_genre:
                    movie_genre_data = MovieGenre(movie_id=movie_id,genre_id=int(g))
                    db.session.add(movie_genre_data)

            db.session.commit()

            flash('Movie has been succesfully added')
            return redirect('/admin/movies/')

    return render_template('admin/admin_add_movie.html', movieform=movieform,actor=actor,producer=producer,studio=studio,genre=genre)

##admin can update the values of a movie in this route
@app.route('/admin/movie/update/<int:id>/', methods=['GET','POST'])
def update_movies(id):
    movie = db.session.query(Movie).get(id)
    actors = db.session.query(Actor).all()
    actor = db.session.query(Actor).get(id)

    producers = db.session.query(Producer).all()
    studio = db.session.query(Studio).all()
    genre = db.session.query(Genre).all()

    movieform = MovieForm()
    if movieform.validate_on_submit():
        title = request.form.get('title')
        release_date= request.form.get('release_date')
        summary = request.form.get('description')
        movie_actor = request.form.get('actor')
        movie_producer=request.form.get('producer')
        movie_studio = request.form.get('studio')
        movie_genre = request.form.getlist('genre')
        poster = request.files.get('poster')
        trailer = request.files.get('trailer')

        ##getting the filenames
        if poster and poster.filename:
            poster_filename = poster.filename
            poster_ext = os.path.splitext(poster_filename)
            extension1 = poster_ext[-1]
    
            ##generating new names
            poster_name = secrets.token_hex(10)
            poster.save("rateflix/static/uploads/poster/"+poster_name+extension1)
            movie.movie_poster = poster_name+extension1
           
        
        if trailer and trailer.filename:
            trailer_filename = trailer.filename
            trailer_ext = os.path.splitext(trailer_filename)
            extension2 = trailer_ext[-1]

            trailer_name = secrets.token_hex(10)
            trailer.save("rateflix/static/uploads/trailers/"+trailer_name+extension2)
            movie.movie_trailer = trailer_name+extension2

        ##updating data in the database
        movie.movie_title = title
        movie.movie_release_date = release_date
        movie.movie_description = summary
        movie.production_studio = movie_studio
        movie.producer_id = movie_producer
        # movie.movie_status = 'approved'

       # Get all existing actors related to the movie
        movieactors = MovieActor.query.filter_by(movie_id=id).all()

        # Create a set of existing actor IDs for the current movie
        existing_actor_ids = {ma.actor_id for ma in movieactors}

        # List of actor IDs to add (assuming 'movie_actor' is a list of actor IDs from the form)
        for actor_id in movie_actor: 
            actor_id = int(actor_id)  

            # Check if the actor is already related to the movie
            if actor_id not in existing_actor_ids:
                # Actor is not yet added to this movie, so add it
                new_movie_actor = MovieActor(movie_id=id, actor_id=actor_id)
                db.session.add(new_movie_actor)

        ##this checks if the movie already has genres before updating
        moviegenres = MovieGenre.query.filter_by(movie_id=id).all()

        # Create a set of existing genre IDs for the current movie
        existing_genre_ids = {mg.genre_id for mg in moviegenres}

        # Loop through the genre IDs provided in the form (assuming movie_genre is a list of genre IDs)
        for genre_id in movie_genre:
            genre_id = int(genre_id)  

            # Check if the genre is already related to the movie
            if genre_id not in existing_genre_ids:
                # Genre is not yet added to this movie, so add it
                new_movie_genre = MovieGenre(movie_id=id, genre_id=genre_id)
                db.session.add(new_movie_genre)

        db.session.commit()
        flash('Movie has been updated and approved')
        return redirect('/admin/movies/')
             
    return render_template('admin/update_movie.html', movie=movie, movieform=movieform,  actor=actor, all_actors=actors, producers=producers,studio=studio, genre=genre)

##route to see the genres of a movie
@app.route('/admin/movie/genre/<int:id>/')
def movie_genres(id):
    movie = Movie.query.get(id)
    genres = MovieGenre.query.filter(MovieGenre.movie_id == id).all()
    return render_template('admin/view_movie_genres.html',movie=movie,genres=genres)

## route to add a new genre to a movie
@app.route('/admin/addgenre/<int:id>/', methods=['GET','POST'])
def admin_addgenre(id):
    movie = Movie.query.get(id)
    genres = Genre.query.all()

    ##list to get all the ids of the current movie
    movie_genre_ids = [mg.genre_id for mg in MovieGenre.query.filter(MovieGenre.movie_id == id).all()]

    if request.method == "POST":
        genre = request.form.getlist('genre')

        for g in genre:
            new_genres = MovieGenre(movie_id=id, genre_id=int(g))

            db.session.add(new_genres)
            db.session.commit()

            flash('Genre has been added')
            return redirect(url_for('movie_genres', id=id))  
        
    return render_template('admin/add_moviegenre.html', movie=movie, genres=genres,movie_genre_ids=movie_genre_ids)

##route to delete a genre from a movie
@app.route('/admin/delgenre/<int:id>/<int:id2>')
def admin_delgenre(id,id2):
    movie = Movie.query.get(id)
    genre = MovieGenre.query.filter(MovieGenre.movie_id == id,MovieGenre.genre_id==id2).first()

    return render_template('admin/del_movie_genre.html',movie=movie,genre=genre)

##confirm genre deletion
@app.route('/admin/delgenre/confirm/<int:id>/<int:id2>/')
def admin_confirm_delgenre(id,id2):
    genre = MovieGenre.query.filter(MovieGenre.movie_id == id,MovieGenre.genre_id==id2).first()

    if genre:
        db.session.delete(genre)
        db.session.commit()
    
    flash('Genre has been deleted')
    return redirect(url_for('movie_genres', id=id))

##route to see all the actors of a movie
@app.route('/admin/movie/actors/<int:id>/')
def movie_actors(id):
    movie = Movie.query.get(id)
    actors = MovieActor.query.filter(MovieActor.movie_id == id).all()
    return render_template('admin/view_movie_actors.html',movie=movie,actors=actors)

## route to add a new actor to a movie
@app.route('/admin/addactor/<int:id>/',methods=['GET','POST'])
def admin_addactor(id):
    movie = Movie.query.get(id)
    actors = db.session.query(Actor).all()
    if request.method == 'POST':
        name = request.form.get('actor')
        add_actor = MovieActor(movie_id=id,actor_id=name)
        
        db.session.add(add_actor)
        db.session.commit()

        flash('Actor has been added')
        return redirect(url_for('movie_actors', id=id))

    return render_template('admin/add_movieactor.html', movie=movie, all_actors=actors)

##route to delete actor from movie
@app.route('/admin/delactor/<int:id>/<int:id2>')
def admin_delactor(id,id2):
    movie = Movie.query.get(id)
    actors = MovieActor.query.filter(MovieActor.actor_id == id2 , MovieActor.movie_id == id).first()

    return render_template('admin/del_movie_actor.html', actors=actors,movie=movie)

##this confirms the deletion
@app.route('/admin/delactor/confirm/<int:id>/<int:id2>')
def admin_confirm_delactor(id,id2):
    actors = MovieActor.query.filter(MovieActor.actor_id == id2 , MovieActor.movie_id == id).first()

    if actors:
        db.session.delete(actors)
        db.session.commit()

    flash('Actor has been deleted')
    return redirect(url_for('movie_actors', id=id))

## route to view all the actors in the database
@app.route('/admin/actors/')
def admin_actors():
    actors = Actor.query.all()
    # details = ActorDetail()
    return render_template('admin/movie_actors.html',actors=actors)

## route to add a new actor to the database
@app.route('/admin/actors/add/', methods=['GET','POST'])
def add_actors():
    details = ActorDetail()
    ## checking if actors exists
    if details.validate_on_submit():
        name = request.form.get('name')
        bio = request.form.get('bio')
        picture = request.files.get('picture')

        actor_photo = 'default_actor.jpg'

        if picture and picture.filename != '':
            ##getting the filenames
            actor_filename = picture.filename

            actor_ext = os.path.splitext(actor_filename)
            extension = actor_ext[-1]
        
            ##generating new names
            actor_name = secrets.token_hex(10)
            picture.save("rateflix/static/uploads/actors/"+actor_name+extension)
            actor_photo = actor_name+extension

        actors = Actor(actor_name=name,actor_bio=bio,actor_photo=actor_photo)

        db.session.add(actors)
        db.session.commit()

        flash('Actor has been added')
        return redirect('/admin/actors/')


    return render_template('admin/add_actor.html',details=details)

## route for updating actor details
@app.route('/admin/actors/update/<int:id>/',methods=['GET','POST'])
def update_actor(id):
    actor = Actor.query.get(id)
    details = ActorDetail()

    if details.validate_on_submit():
        name = request.form.get('name')
        bio = request.form.get('bio')
        picture = request.files.get('picture')

        if picture and picture.filename != '':
            ##getting the filenames
            actor_filename = picture.filename

            
            actor_ext = os.path.splitext(actor_filename)
            extension = actor_ext[-1]
        
            ##generating new names
            actor_name = secrets.token_hex(10)
            picture.save("rateflix/static/uploads/actors/"+actor_name+extension)
            actor.actor_photo = actor_name+extension

        ## uppdating the actor details
        actor.actor_name = name
        actor.actor_bio = bio
        db.session.commit()

        flash('Actor has been updated')
        return redirect('/admin/actors/')
    
    return render_template('admin/update_actor.html',details=details, actor=actor)

##route for deleting an actor
@app.route('/admin/actors/delete/<int:id>/')
def delete_actor(id):
    actor = Actor.query.get(id)
    return render_template('admin/delete_actor.html',actor=actor)

##route to confirm delete
@app.route('/confirm/delete/actor/<int:id>')
def confirm_actor_delete(id):
    actor = Actor.query.get(id)

    if actor:
        db.session.delete(actor)
        db.session.commit()
    
    flash('Actor has been deleted')
    return redirect('/admin/actors/')


## route to see more producers
@app.route('/admin/producers/')
def admin_producers():
    producers = Producer.query.all()

    return render_template('admin/admin_producers.html', producers=producers)

## route for adding produce
@app.route('/admin/producers/add/', methods=['GET','POST'])
def add_producer():
    producer = ProducerDetail()

    ##check if producer exists
    if producer.validate_on_submit():
        name = request.form.get('name')

        add_producer = Producer(producer_name=name)

        db.session.add(add_producer)
        db.session.commit()

        flash('Producer has been added')
        return redirect('/admin/producers/')

    return render_template('admin/add_producer.html', producer=producer)


## this is the route for updating producer details
@app.route('/admin/producers/update/<int:id>/', methods=['GET','POST'])
def update_producer(id):
    producerdetails = Producer.query.get(id)
    producer = ProducerDetail()

    if producer.validate_on_submit():
        name = request.form.get('name')

        producerdetails.producer_name = name

        db.session.commit()

        flash('Producer has been updated')
        return redirect('/admin/producers/')
    
    return render_template('admin/update_producer.html',producerdetails=producerdetails,producer=producer)

##this route is for deleting a producer
@app.route('/admin/delete/producer/<int:id>/')
def delete_producer(id):
    producer = Producer.query.get(id)
    return render_template('admin/delete_producer.html',producer=producer)

##route for confirming the deletion of a producer
@app.route('/confirm/delete/producer/<int:id>/')
def confirm_delete_producer(id):
    producer = Producer.query.get(id)

    if producer:
        db.session.delete(producer)
        db.session.commit()
    
    flash('producer has been deleted')
    return redirect('/admin/producers/')

##this route is for displaying all genres
@app.route('/admin/genres/')
def admin_genre():
    genres = Genre.query.all()
    return render_template('admin/admin_genre.html', genres=genres)

## this route is for adding new genres
@app.route('/admin/genre/add/', methods=['GET','POST'])
def add_genre():
    genre = GenreDetail()

    ## check if genre exists
    if genre.validate_on_submit():
        name = request.form.get('name')

        genredetails = Genre(genre_name=name)
        
        db.session.add(genredetails)
        db.session.commit()

        flash('Genre has been added')
        return redirect('/admin/genres/')
    return render_template('admin/add_genre.html' ,genre=genre )

## this is the route for deleting a genre
@app.route('/admin/delete/genre/<int:id>/')
def admin_delete_genre(id):
    genre = Genre.query.get(id)
    return render_template('admin/delete_genre.html',genre=genre)

## this routes confirms the deletion of genre
@app.route('/confirm/delete/genre/<int:id>/')
def confirm_delete_genre(id):
    genre = Genre.query.get(id)

    if genre:
        db.session.delete(genre)
        db.session.commit()
    
    flash('Genre has been deleted')
    return redirect('/admin/genres/')
