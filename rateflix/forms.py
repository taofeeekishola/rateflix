from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,DateField,TextAreaField,SelectMultipleField
from flask_wtf.file import FileField, FileAllowed,FileRequired
from wtforms.validators import DataRequired, Email, EqualTo


class Login(FlaskForm):
    email = StringField('Email',validators=[DataRequired(message='Please enter your email'), Email(message='Please enter a valid email')])
    password = PasswordField('Password',validators=[DataRequired(message='Please enter your password')])
    login = SubmitField('Login')


class Register(FlaskForm):
    first_name = StringField('First Name',validators=[DataRequired(message='Please enter your First Name')])
    last_name = StringField('Last Name',validators=[DataRequired(message='Please enter your Last Name')])
    user_name = StringField('User Name',validators=[DataRequired(message='Enter a Username')])
    email = StringField('Email',validators=[DataRequired(message='Please enter your email'),Email(message='Please enter a valid email')])
    password = PasswordField('Password',validators=[DataRequired(message='Please enter your password')])
    con_password = PasswordField('Confirm Password',validators=[DataRequired(message='Please enter your password'), EqualTo('password',message='Password must be the same')])
    profile_picture  = FileField("Profile Picture",validators=[FileAllowed(["jpg","png"],"Invalid File Format")])
    date_of_birth = DateField('Date of birth', format='%Y-%m-%d')
    signup = SubmitField('Sign Up')

    
class UpdateProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(message='Please enter your First Name')])
    last_name = StringField('Last Name', validators=[DataRequired(message='Please enter your Last Name')])
    profile_picture = FileField("Profile Picture", validators=[FileAllowed(["jpg", "png"], "Invalid File Format")])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d')
    update = SubmitField('Update')

class MovieForm(FlaskForm):
    title = StringField('Title',validators=[DataRequired(message='Enter the title of the movie')])
    release_date = DateField('Release Date', format='%Y-%m-%d')
    description = TextAreaField('Plot Summary')
    poster  = FileField("Poster",validators=[FileAllowed(["jpg","png"],"Invalid File Format")])
    trailer = FileField("Trailer",validators=[FileAllowed(["mp4"],"Invalid File Format")])
    producer = StringField('Producer')
    studio = StringField('Production Studio',validators=[DataRequired(message="Studio missing")])
    submit = SubmitField('Submit')


class MovieReview(FlaskForm):
    review = TextAreaField("Review")
    submit_review = SubmitField('Submit')

class ActorDetail(FlaskForm):
    name = StringField('First Name',validators=[DataRequired(message='Actor name required')])
    bio = TextAreaField('Last Name')
    picture = FileField('Picture',validators=[FileAllowed(["jpg","png"],"Invalid File Format")])
    add = SubmitField('Add')

class ProducerDetail(FlaskForm):
    name = StringField('Full Name',validators=[DataRequired(message='Producer name is required')])
    add = SubmitField('Add')

class GenreDetail(FlaskForm):
    name = StringField('Full Name',validators=[DataRequired(message='Genre name is required')])
    add = SubmitField('Add')

class StudioDetail(FlaskForm):
    name = StringField('Full Name',validators=[DataRequired(message='Studio name is required')])
    add = SubmitField('Add')