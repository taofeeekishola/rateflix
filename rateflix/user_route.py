import secrets,os
from flask import render_template,request,redirect,flash,url_for,session,jsonify
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import extract

from rateflix import app
from rateflix.forms import Register,Login,MovieForm,MovieReview,UpdateProfileForm
from rateflix.models import db,Member,Studio,Producer,Genre,Actor,Movie,MovieActor,MovieGenre,Review,Rating

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
                profile_picture.save("rateflix/static/uploads/profile_pic/"+profile_picture_name+extension)
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

            movie_details = Movie(movie_title=title,producer_id=movie_producer,movie_release_date=release_date,movie_description=summary,production_studio=movie_studio)

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
    ratings = Rating.query.filter(Rating.movie_id == id).all()
    moviess = Movie.query.filter(Movie.movie_status == 'approved').all()
    
    genre_ids = [genre.genre_id for genre in genres]

    ## getting all the movies with the same genres as the movie the member is reading about
    similar_movies = (
            Movie.query.join(MovieGenre, Movie.movie_id == MovieGenre.movie_id).filter(MovieGenre.genre_id.in_(genre_ids),Movie.movie_status == 'approved',Movie.movie_id != id).limit(5)
        )
    
    if ratings:
        total_ratings = sum(r.rating_score for r in ratings)
        average_rating = total_ratings / len(ratings)
    else:
        average_rating = 0
  

    ##user review form
    review = MovieReview()

    data = session.get('member_id')
    if data != None:
        user_session = get_user_byid(data)

    else:
        user_session = None
    all_reviews = db.session.query(Review).filter(Review.movie_id == id).order_by(Review.review_date.desc()).all()

    return render_template('user/movie.html',user_session=user_session,movies=movies,actors=actors,genres=genres,review=review,all_reviews=all_reviews,average_rating=average_rating,moviess=similar_movies)

##route is used to submit reviews
@app.route('/ajax/movie/review/',methods=['POST'])
def submit_review():
    review = request.form.get('reviewData')
    movieid = request.form.get('movieId')
    data = session.get('member_id')
    member = Member.query.get(data)

    user_review = Review(member_id=data, movie_id=movieid, review_content=review)
    db.session.add(user_review)
    db.session.commit()

    all_reviews = Review.query.filter(Review.movie_id == movieid).all()

 
    # Return only the newly submitted review
    return jsonify({
        'member_username':member.member_username,
        'review_content': user_review.review_content,
        'review_date': user_review.review_date.strftime('%Y-%m-%d %H:%M:%S')
    })


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
    try:
        rating = request.form.get('rating')
        movieid = request.form.get('movieId')
        data = session.get('member_id')

        if not rating or not movieid or not data:
            raise ValueError("Missing data")
        
        # Check if the user has already rated this movie
        existing_rating = Rating.query.filter_by(member_id=data, movie_id=movieid).first()
        if existing_rating:
            return jsonify({'message': 'You have already rated this movie'}), 200

        user_rating = Rating(member_id=data, movie_id=movieid, rating_score=rating)
        db.session.add(user_rating)
        db.session.commit()

        return jsonify({'message': f'Rating {rating} received successfully!'})

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
   