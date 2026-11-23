import secrets,os
from datetime import datetime
from flask import render_template,request,redirect,flash,url_for,session,jsonify,abort
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

## average rating and number of ratings for several movies at once: {movie_id: (average, count)}
def rating_summaries(movie_ids):
    movie_ids = list(movie_ids)
    if not movie_ids:
        return {}
    rows = (db.session.query(Rating.movie_id, db.func.avg(Rating.rating_score), db.func.count(Rating.rating_id))
            .filter(Rating.movie_id.in_(movie_ids))
            .group_by(Rating.movie_id))
    return {movie_id: (round(float(average), 1), count) for movie_id, average, count in rows}

## approved movies, narrowed by release year, genre and studio in any combination, newest first
def browse_movies(year=None, genre=None, studio=None):
    query = Movie.query.filter(Movie.movie_status == 'approved')
    if year:
        query = query.filter(extract('year', Movie.movie_release_date) == year)
    if genre:
        query = query.filter(Movie.genres.any(MovieGenre.genre_id == genre))
    if studio:
        query = query.filter(Movie.production_studio == studio)
    return query.order_by(Movie.movie_release_date.desc(), Movie.movie_id.desc()).all()

## the movie at the top of the home page: the highest rated movie that has a poster
## (ties go to the one with more ratings). If nobody has rated anything yet, the newest movie.
## Returns (movie, is_top_rated)
def featured_movie():
    has_poster = (Movie.movie_status == 'approved', Movie.movie_poster.isnot(None), Movie.movie_poster != '')
    ratings = (db.session.query(Rating.movie_id.label('movie_id'),
                                db.func.avg(Rating.rating_score).label('average'),
                                db.func.count(Rating.rating_id).label('total'))
               .group_by(Rating.movie_id)
               .subquery())
    top = (Movie.query.join(ratings, ratings.c.movie_id == Movie.movie_id)
           .filter(*has_poster)
           .order_by(ratings.c.average.desc(), ratings.c.total.desc(), Movie.movie_release_date.desc())
           .first())
    if top:
        return top, True
    newest = (Movie.query.filter(*has_poster)
              .order_by(Movie.movie_release_date.desc(), Movie.movie_id.desc())
              .first())
    return newest, False

## posters for the background of the log in and sign up pages
def poster_wall(limit=12):
    movies = (Movie.query.filter(Movie.movie_status == 'approved', Movie.movie_poster.isnot(None), Movie.movie_poster != '')
              .order_by(Movie.movie_release_date.desc())
              .limit(limit))
    return [m.movie_poster for m in movies]

##funcion to always retrive the user id
def get_user_byid(id):
    data = Member.query.get(id)
    return data

##home page route
## the filters can come in the address too (e.g. /?genre=3 from a genre on a movie page)
@app.route('/')
def home():
    selected = {
        'year': request.args.get('year', type=int),
        'genre': request.args.get('genre', type=int),
        'studio': request.args.get('studio', type=int),
    }
    movies = browse_movies(**selected)
    featured, featured_is_top = featured_movie()

    genres = Genre.query.order_by(Genre.genre_name).all()
    studio = Studio.query.order_by(Studio.studio_name).all()
    release_dates = db.session.query(Movie.movie_release_date).filter(Movie.movie_status == 'approved', Movie.movie_release_date.isnot(None))
    years = sorted({d.year for (d,) in release_dates}, reverse=True)
    total = Movie.query.filter(Movie.movie_status == 'approved').count()

    movie_ids = [m.movie_id for m in movies] + ([featured.movie_id] if featured else [])
    scores = rating_summaries(movie_ids)

    ## this checks if the session is empty and allows us to use it to create a database object and access the data in the home page
    data = session.get('member_id')
    if data != None:
        user_session = get_user_byid(data)
    else:
        user_session = None

    return render_template('user/index.html', user_session=user_session, movies=movies, genres=genres, studio=studio,
                           years=years, selected=selected, total=total, scores=scores,
                           featured=featured, featured_is_top=featured_is_top)

## search movies by title
@app.route('/search/')
def search():
    q = (request.args.get('q') or '').strip()
    movies = []
    if q:
        ## treat % and _ as normal characters, not wildcards
        pattern = '%' + q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        movies = (Movie.query.filter(Movie.movie_status == 'approved', Movie.movie_title.ilike(pattern, escape='\\'))
                  .order_by(Movie.movie_title)
                  .all())
    scores = rating_summaries(m.movie_id for m in movies)
    return render_template('user/search.html', q=q, movies=movies, scores=scores)

##this checks if the username already exists in the database and displays the options using ajax
@app.route('/user/valusername/')
def valusername():
    username = request.args.get('username')
    data = db.session.query(Member).filter(Member.member_username == username).first()

    if data:
        return 'Username is taken'
    else:
        return 'Username is available'

##checking if the email already exists in the database
@app.route('/user/emailval/')
def emailval():
    email = request.args.get('email')
    data = Member.query.filter(Member.member_email == email).first()

    if data:
        return 'Email is taken'
    else:
        return 'Email is available'

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
            db.session.rollback()
            flash('That email or username is already taken.')
            return redirect('/user/signup/')


    return render_template('user/signup.html', signup=signup, posters=poster_wall())

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
                flash('Incorrect password.')
                redirect('/user/login/')
        else:
            flash('No account uses that email.')
            redirect('/user/login/')

    return render_template('user/login.html', login=login, posters=poster_wall())

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
    movies = Movie.query.filter(Movie.movie_status=='approved', Movie.added_by == data).order_by(Movie.movie_release_date.desc()).all()

    if data != None:
        user_session = get_user_byid(data)

    else:
        flash('You need to login to access this page')
        return redirect('/user/login/')

    pending = Movie.query.filter(Movie.movie_status == 'pending', Movie.added_by == data).count()
    reviews = Review.query.filter(Review.member_id == data).count()
    ratings = Rating.query.filter(Rating.member_id == data).count()
    scores = rating_summaries(m.movie_id for m in movies)

    return render_template('user/profile.html', user_session=user_session, moviess=movies, scores=scores,
                           pending=pending, review_count=reviews, rating_count=ratings)

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
            dob = update.date_of_birth.data   # a date, or None when left empty

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
            movie_producer=request.form.get('producer') or None   # "Not listed"
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
    if movies is None:
        abort(404)
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
    scores = rating_summaries(m.movie_id for m in similar_movies)

    return render_template('user/movie.html',user_session=user_session,movies=movies,actors=actors,genres=genres,review=review,all_reviews=all_reviews,average_rating=average_rating,rating_count=rating_count,my_rating=my_rating,moviess=similar_movies,scores=scores)

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
        'member_profile_pic': member.member_profile_pic,
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
            movie_actor = [a for a in request.form.getlist('actor') if a]   # actor ids; empty means "no change"
            movie_producer=request.form.get('producer') or None   # "Not listed"
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
## the filters can be combined (e.g. 2024 + Animation). Returns the cards as HTML for the home page grid.
def filter_movies():
    movies = browse_movies(year=request.args.get('year', type=int),
                           genre=request.args.get('genre', type=int),
                           studio=request.args.get('studio', type=int))
    scores = rating_summaries(m.movie_id for m in movies)
    return render_template('user/_movie_grid.html', movies=movies, scores=scores, filtered=True)
    
   
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
    
   