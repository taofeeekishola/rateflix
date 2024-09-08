import os,secrets
from flask import render_template,redirect,flash,request,session

from rateflix import app
from rateflix.forms import Register,Login,MovieForm,MovieReview,ActorDetail,ProducerDetail
from rateflix.models import db,Member,Studio,Producer,Genre,Actor,Movie,MovieActor,MovieGenre,Review

@app.route('/admin/')
def admin():
    return render_template('admin/admin.html')

@app.route('/admin/movies/')
def admin_movies():
    movies = db.session.query(Movie).all()
    # movie_genre = db.session.query(MovieGenre).all()
    return render_template('admin/all_movies.html', movies=movies)

##admin can update the values of a movie in this route
@app.route('/admin/movie/update/<int:id>/', methods=['GET','POST'])
def update_movies(id):
    movie = db.session.query(Movie).get(id)
    actors = db.session.query(Actor).all()
    actor = db.session.query(Actor).get(id)

    producers = db.session.query(Producer).all()
    studio = db.session.query(Studio).all()
    genre = db.session.query(Genre).all()

    movieactors = MovieActor.query.get(id)
    moviegenres = MovieGenre.query.get(id)
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
        poster_filename = poster.filename
        trailer_filename = trailer.filename
        
        poster_ext = os.path.splitext(poster_filename)
        extension1 = poster_ext[-1]
        trailer_ext = os.path.splitext(trailer_filename)
        extension2 = trailer_ext[-1]

        ##generating new names
        poster_name = secrets.token_hex(10)
        poster.save("rateflix/static/uploads/poster/"+poster_name+extension1)

        trailer_name = secrets.token_hex(10)
        trailer.save("rateflix/static/uploads/trailers/"+trailer_name+extension2)

        ##updating data in the database
        movie.movie_title = title
        movie.movie_release_date = release_date
        movie.movie_description = summary
        movie.production_studio = movie_studio
        movie.producer_id = movie_producer
        movie.movie_poster = poster_name+extension1
        movie.movie_trailer = trailer_name+extension2
        movie.movie_status = 'approved'

        ##this checks if the movie already has actors before updating
        if movieactors != None:
            movieactors.movie_id = id
            movieactors.actor_id = movie_actor
        else:
            addmovieactors = MovieActor(movie_id=id, actor_id=movie_actor)
            db.session.add(addmovieactors)

        ##this checks if the movie already has genres before updating
        if moviegenres != None:
            for g in moviegenres:
                moviegenres.movie_id=id
                moviegenres.genre_id=int(g)
        else:
            for g in movie_genre:
                    movie_genre_data = MovieGenre(movie_id=id,genre_id=int(g))
                    db.session.add(movie_genre_data)


        db.session.commit()
        flash('Movie has been updated and approved')
        return redirect('/admin/movies/')
            
        
    return render_template('admin/update_movie.html', movie=movie, movieform=movieform,  actor=actor, all_actors=actors, producers=producers,studio=studio, genre=genre)

## route to view all the actors
@app.route('/admin/actors/')
def admin_actors():
    actors = Actor.query.all()
    # details = ActorDetail()
    return render_template('admin/movie_actors.html',actors=actors)

## route to add a new actor to the database
@app.route('/admin/actors/add/', methods=['GET','POST'])
def add_actors():
    details = ActorDetail()
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


## route to add more producers
@app.route('/admin/producers/')
def admin_producers():
    producers = Producer.query.all()

    return render_template('admin/admin_producers.html', producers=producers)

## route for adding produce
@app.route('/admin/producers/add/', methods=['GET','POST'])
def add_producer():
    producer = ProducerDetail()
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

