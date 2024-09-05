from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,DateField,TextAreaField,SelectField
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
    signup = SubmitField('Sign Up')

class MovieForm(FlaskForm):
    title = StringField('Title',validators=[DataRequired(message='Enter the title of the movie')])
    release_date = DateField('Release Date', format='%Y-%m-%d')
    description = TextAreaField('Plot Summary')
    # actor = SelectField('Actor', coerce=int, validators=[DataRequired()])
    producer = StringField('Producer')
    studio = StringField('Production Studio',validators=[DataRequired(message="Studio missing")])
    submit = SubmitField('Submit')

class Review(FlaskForm):
    review = TextAreaField("Review")
    submit = SubmitField('Submit')
