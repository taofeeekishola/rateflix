import secrets,os
from datetime import datetime
from flask import render_template,request,redirect,flash,url_for,session,jsonify
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import extract

from rateflix import app, upload_path
from rateflix.forms import Register,Login,MovieForm,MovieReview,UpdateProfileForm
from rateflix.models import db,Member,Studio,Producer,Genre,Actor,Movie,MovieActor,MovieGenre,Review,Rating

## a movie's average rating (rounded to 1 decimal) and how many ratings it has
def movie_rating_summary(movie_id):
    average, count = db.session.query(db.func.avg(Rating.rating_score), db.func.count(Rating.rating_id)).filter(Rating.movie_id == movie_id).one()
    return (round(float(average), 1) if average is not None else 0), count

## "More like this": approved movies ranked by how many genres they share with this one,
## then by RateFlix rating, then newest first. Each movie appears once, and if fewer than
## `limit` movies share a genre, the rest of the slots are filled with the next best movies.
def similar_movies_for(movie_id, limit=5):
    genre_ids = [g.genre_id for g in MovieGenre.query.filter_by(movie_id=movie_id)]

    shared = (db.session.query(MovieGenre.movie_id.label('movie_id'), db.func.count(MovieGenre.genre_id).label('shared'))
              .filter(MovieGenre.genre_id.in_(genre_ids))
              .group_by(MovieGenre.movie_id)
              .subquery())
    ratings = (db.session.query(Rating.movie_id.label('movie_id'), db.func.avg(Rating.rating_score).label('average'))
               .group_by(Rating.movie_id)
               .subquery())

    return (Movie.query
            .outerjoin(shared, shared.c.movie_id == Movie.movie_id)
            .outerjoin(ratings, ratings.c.movie_id == Movie.movie_id)
            .filter(Movie.movie_status == 'approved', Movie.movie_id != movie_id)
            .order_by(db.func.coalesce(shared.c.shared, 0).desc(),
                      db.func.coalesce(ratings.c.average, 0).desc(),
                      Movie.movie_release_date.desc(),
                      Movie.movie_id.desc())
            .limit(limit)
            .all())

##funcion to always retrive the user id
def get_user_byid(id):
    data = Member.query.get(id)
    return data

##home page route
@app.route('/')
def home():
    movies = Movie.query.filter(Movie.movie_status == 'approved').all()
    genres = Genre.query.all()
    studio = Studio.query.all()
    ratings = Rating.query.all()

    ## this checks if the session is empty and allows us to use it to create a database object and access the data in the home page
    data = session.get('member_id')
    if data != None:
        user_session = get_user_byid(data)
    else:
        user_session = None

    return render_template('user/index.html' ,user_session=user_session,movies=movies,genres=genres,studio=studio,ratings=ratings)

##this checks if the username already exists in the database and displays the options using ajax
@app.route('/user/valusername/')
def valusername():
    username = request.args.get('username')
    data = db.session.query(Member).filter(Member.member_username == username).first()

    if data:
        return 'Username is taken'
    else:
        return 'Username is avaliable'

##checking if the email already exists in the database
@app.route('/user/emailval/')
def emailval():
    email = request.args.get('email')
    data = Member.query.filter(Member.member_email == email).first()

    if data:
        return 'Email is taken'
    else:
        return 'Email is avaliable'

##user signup page
@app.route('/user/signup/',methods=['GET','POST'])
def user_signup():
    signup = Register()
    if signup.validate_on_submit():
        firstname = request.form.get('first_name')
        lastname = request.form.get('last_name')
        username = request.form.get('user_name')
        email = request.form.get('email')
        password = request.form.get('password')

        hashed = generate_password_hash(password)

        data = Member(member_firstname=firstname,member_lastname=lastname,member_username=username,member_email=email,member_password=hashed)

        try:
            ## storing the data into the database
            db.session.add(data)
            db.session.commit()

            ##using the id of the user to create a session
            session['member_id'] = data.member_id
            return redirect('/')
        except:
            flash('Email or Username Taken')
            return redirect('/user/signup/')


    return render_template('user/signup.html', signup=signup)

##the login page
@app.route('/user/login/', methods=['GET','POST'])
def user_login():
    login = Login()
    if login.validate_on_submit():
        email = request.form.get('email')
        password = request.form.get('password')

        data = db.session.query(Member).filter(Member.member_email == email).first()
        if data:
            hashed_password = data.member_password
            pass_check = check_password_hash(hashed_password,password)
            if pass_check:
                session['member_id'] = data.member_id
                return redirect('/user/profile/')
            else:
                flash('Incorrect Pasword')
                redirect('/user/login/')
        else:
            flash('Incorrect Email')
            redirect('/user/login/')

    return render_template('user/login.html' ,login=login)

##this logs the user out
@app.route('/user/logout/')
def user_logout():
    if session.get('member_id') != None:
        session.pop('member_id')
        
    flash('You are now logged out','success')
    return redirect('/')

## route to visit user profile page
@app.route('/user/profile/')
def user_page():
    data = session.get('member_id')
    movies = Movie.query.filter(Movie.movie_status=='approved', Movie.added_by == data)

    if data != None:
        user_session = get_user_byid(data)
        
    else:
        flash('You need to login to access this page')
        return redirect('/user/login/')
    
    return render_template('user/profile.html' ,user_session=user_session,moviess=movies)

## route to allow users update profile
@app.route('/user/update/profile/',methods=['GET','POST'])
def user_profile_update():
    update = UpdateProfileForm()
    data = session.get('member_id')

    if data != None:
        user_session = get_user_byid(data)
        
        if update.validate_on_submit():
            firstname = request.form.get('first_name')
            lastname = request.form.get('last_name')
            profile_picture = request.files.get('profile_picture')
            bio = request.form.get('bio')
            dob = request.form.get('date_of_birth')

            ## checking if profile_picture was provided
            if profile_picture and profile_picture.filename:
                profile_picture_filename = profile_picture.filename
                profile_picture_ext = os.path.splitext(profile_picture_filename)
                extension = profile_picture_ext[-1]
        
                ##generating new names
                profile_picture_name = secrets.token_hex(10)
                profile_picture.save(upload_path('profile_pic', profile_picture_name+extension))
                user_session.member_profile_pic = profile_picture_name+extension
            
            user_session.member_firstname = firstname
            user_session.member_lastname = lastname
            user_session.member_bio = bio
            user_session.member_date_of_birth = dob

            db.session.commit()
            
            flash('Profile has been updated')
            return redirect('/user/profile/')
    else:
        flash('You need to login to access this page')
        return redirect('/user/login/')
    
    return render_template('user/update_profile.html',user_session=user_session,update=update)


## the route users use to add movies to the database
@app.route('/user/add_movie/', methods=['GET','POST'])
def user_addmovie():
    data = session.get('member_id')
    movie = MovieForm()
    producer = db.session.query(Producer).all()
    studio = db.session.query(Studio).all()
    genre = db.session.query(Genre).all()
    actor = db.session.query(Actor).all()
    if data != None:
        user_session = get_user_byid(data)

        if movie.validate_on_submit():
            title = request.form.get('title')
            release_date= request.form.get('release_date')
            summary = request.form.get('description')
            movie_actor = request.form.get('actor')
            movie_producer=request.form.get('producer')
            movie_studio = request.form.get('studio')
            movie_genre = request.form.getlist('genre')

            movie_details = Movie(movie_title=title,producer_id=movie_producer,movie_release_date=release_date,movie_description=summary,production_studio=movie_studio,added_by=data)

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
            return redirect('/user/add_movie/')


        return render_template('user/add_movie.html' ,user_session=user_session,movie=movie,producer=producer,studio=studio,genre=genre,actor=actor)
    else:
        flash('You need to login to access this page')
        return redirect('/user/login/')
    

## this route will have information about the movie
@app.route('/movie/info/<int:id>',methods=['GET','POST'])
def movie_info(id):
    movies = Movie.query.get(id)
    actors = MovieActor.query.filter(MovieActor.movie_id == id).all()
    genres = MovieGenre.query.filter(MovieGenre.movie_id == id).all()

    ## "More like this": movies that share the most genres with this one
    similar_movies = similar_movies_for(id)

    average_rating, rating_count = movie_rating_summary(id)

    ##user review form
    review = MovieReview()

    data = session.get('member_id')
    my_rating = 0
    if data != None:
        user_session = get_user_byid(data)
        mine = Rating.query.filter_by(member_id=data, movie_id=id).first()
        if mine:
            my_rating = mine.rating_score

    else:
        user_session = None
    all_reviews = db.session.query(Review).filter(Review.movie_id == id).order_by(Review.review_date.desc()).all()

    return render_template('user/movie.html',user_session=user_session,movies=movies,actors=actors,genres=genres,review=review,all_reviews=all_reviews,average_rating=average_rating,rating_count=rating_count,my_rating=my_rating,moviess=similar_movies)

##route is used to submit reviews
@app.route('/ajax/movie/review/',methods=['POST'])
def submit_review():
    data = session.get('member_id')
    member = Member.query.get(data) if data is not None else None
    if member is None:
        return jsonify({'error': 'Please log in to post a review.'}), 401

    review = (request.form.get('reviewData') or '').strip()
    movieid = request.form.get('movieId', type=int)
    if not review:
        return jsonify({'error': 'Please write something before posting.'}), 400
    if movieid is None or Movie.query.get(movieid) is None:
        return jsonify({'error': 'Movie not found.'}), 404

    ## a double click or a slow connection can send the same review twice: keep only one copy
    user_review = Review.query.filter_by(member_id=data, movie_id=movieid, review_content=review).first()
    duplicate = user_review is not None
    if not duplicate:
        user_review = Review(member_id=data, movie_id=movieid, review_content=review)
        db.session.add(user_review)
        db.session.commit()

    # Return only the newly submitted review
    return jsonify({
        'review_id': user_review.review_id,
        'member_username': member.member_username,
        'review_content': user_review.review_content,
        'review_date': user_review.review_date.strftime('%Y-%m-%d'),
        'duplicate': duplicate
    })

##route is used to delete a review: allowed for the person who wrote it and for admins
@app.route('/ajax/movie/review/<int:review_id>/delete/', methods=['POST'])
def delete_review(review_id):
    user_review = Review.query.get(review_id)
    if user_review is None:
        return jsonify({'deleted': True})

    is_author = session.get('member_id') is not None and session.get('member_id') == user_review.member_id
    is_admin = session.get('admin_id') is not None
    if not (is_author or is_admin):
        return jsonify({'error': 'You can only delete your own reviews.'}), 403

    ## replies to the review are removed by the database too (ON DELETE CASCADE)
    Review.query.filter_by(review_id=review_id).delete()
    db.session.commit()
    return jsonify({'deleted': True})


#route to see all the movies user has added
@app.route('/user/movieadded/')
def user_moviesadded():
    data = session.get('member_id')
    movie = Movie.query.filter(Movie.added_by == data)
    if data != None:
        user_session = get_user_byid(data)
    else:
        flash('You need to login')
        return redirect('/user/login/')
    
    return render_template('user/view_movies.html',user_session=user_session , movie=movie)

# route where user can update movies they have added
@app.route('/user/movie/update/<int:id>/', methods=['GET','POST'])
def user_update_movie(id):

    movie = Movie.query.get(id)
    actors = db.session.query(Actor).all()
    producers = db.session.query(Producer).all()
    studio = db.session.query(Studio).all()
    genre = db.session.query(Genre).all()
    data = session.get('member_id')
    movieform = MovieForm()
    if data != None:
        user_session = get_user_byid(data)


        if movieform.validate_on_submit():
            title = request.form.get('title')
            release_date= request.form.get('release_date')
            summary = request.form.get('description')
            movie_actor = request.form.get('actor')
            movie_producer=request.form.get('producer')
            movie_studio = request.form.get('studio')
            movie_genre = request.form.getlist('genre')
           

            ##updating data in the database
            movie.movie_title = title
            movie.movie_release_date = release_date
            movie.movie_description = summary
            movie.production_studio = movie_studio
            movie.producer_id = movie_producer

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
            flash('Movie has been updated')
            return redirect('/user/movieadded/')

    else:
        flash('You need to login')
        return redirect('/user/login/')
    
    return render_template('user/user_update_movie.html',movie=movie,user_session=user_session,movieform=movieform,all_actors=actors,producers=producers,studio=studio,genre=genre)

##route for filtering movies
@app.route('/ajax/movie/filter/', methods=['GET'])
def filter_movies():
    year = request.args.get('year')
    genre = request.args.get('genre')
    studio = request.args.get('studio')

    movies = []
    
    if not year and not genre and not studio:
        movies = Movie.query.filter(Movie.movie_status =='approved').all() 
    
    if year:
        movies = Movie.query.filter(extract('year', Movie.movie_release_date) == int(year),Movie.movie_status =='approved').all()

    if genre:
        movies = Movie.query.join(MovieGenre).filter(MovieGenre.genre_id == int(genre),Movie.movie_status =='approved').all()


    if studio:
        movies = Movie.query.filter(Movie.production_studio == int(studio),Movie.movie_status =='approved').all()
    
    if not movies:
        return '<p>No movies found matching the criteria.</p>'
    
    movie_html = ''.join(
    f'''
    <div class="col-6 col-md-4 col-lg-2 mb-4">
        <div class="card card-custom">
            <a href="/movie/info/{movie.movie_id}"><img src="/static/uploads/poster/{movie.movie_poster}" class="card-img-top poster" alt="{movie.movie_poster}"></a>
            <div class="card-body">
                <a href="/movie/info/{movie.movie_id}"><p class="card-title mb-2 fs-6">{movie.movie_title}</p></a>
                <div class="d-flex justify-content-between align-items-center mb-2 ">
                    <p class="card-text mb-0"></p>
                </div>
                <div class="d-flex justify-content-center align-items-center">
                    <a href="/movie/info/{movie.movie_id}" class="btn btn-primary btn-sm flex-fill me-2 custom-btn"><i class="fa-solid fa-play"></i> Trailer</a>
                </div>
            </div>
        </div>
    </div>
    ''' for movie in movies
    )

    return movie_html
    
   
##route to submit movie rating
@app.route('/user/submitrating/', methods=['POST'])
def user_rating():
    data = session.get('member_id')
    if data is None or Member.query.get(data) is None:
        return jsonify({'error': 'Please log in to rate this movie.'}), 401

    rating = request.form.get('rating', type=int)
    movieid = request.form.get('movieId', type=int)
    if rating is None or not 1 <= rating <= 5:
        return jsonify({'error': 'Please pick between 1 and 5 stars.'}), 400
    if movieid is None or Movie.query.get(movieid) is None:
        return jsonify({'error': 'Movie not found.'}), 404

    ## one rating per person per movie: rating again replaces the old one
    user_rating = Rating.query.filter_by(member_id=data, movie_id=movieid).first()
    if user_rating:
        user_rating.rating_score = rating
        user_rating.rating_date = datetime.utcnow()
    else:
        db.session.add(Rating(member_id=data, movie_id=movieid, rating_score=rating))
    db.session.commit()

    average_rating, rating_count = movie_rating_summary(movieid)
    return jsonify({'your_rating': rating, 'average_rating': average_rating, 'rating_count': rating_count})
    
   