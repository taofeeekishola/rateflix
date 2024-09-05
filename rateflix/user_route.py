from flask import render_template,request,redirect,flash,url_for,session
from werkzeug.security import generate_password_hash,check_password_hash
from rateflix import app
from rateflix.forms import Register,Login,MovieForm,Review
from rateflix.models import db,Member,Studio,Producer,Genre,Actor,Movie,MovieActor,MovieGenre

##funcion to always retrive the user id
def get_user_byid(id):
    data = Member.query.get(id)
    return data

@app.route('/')
def home():
    movies = Movie.query.limit(6)
    ## this checks if the session is empty and allows us to use it to create a database object and access the data in the home page
    data = session.get('member_id')
    if data != None:
        user_session = get_user_byid(data)
    else:
        user_session = None

    return render_template('user/index.html' ,user_session=user_session,movies=movies)

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


"""THE USERPAGE VIEWS"""
@app.route('/user/profile/')
def user_page():
    data = session.get('member_id')
    if data != None:
        user_session = get_user_byid(data)
        return render_template('user/profile.html' ,user_session=user_session)
    else:
        flash('You need to login to access this page')
        return redirect('/user/login/')
    
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
    genres = MovieGenre.query.filter(MovieGenre.movie_genre_id == id).all()
    
    ##user review form
    review = Review()

    data = session.get('member_id')
    if data != None:
        user_session = get_user_byid(data)

        if review.validate_on_submit():
            pass
    else:
        user_session = None

    return render_template('user/movie.html',user_session=user_session,movies=movies,actors=actors,genres=genres,review=review)

    

