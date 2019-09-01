from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, HiddenField, TextField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self,username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please enter a different username')

    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please enter a different email')

class ClockInForm(FlaskForm):
    jobname = SelectField(u'Job Type', choices=[('t1','test1'),('t2','test2')])
    submit = SubmitField('Clock In', id="clockInButton")
    latitude = HiddenField(id="lat")
    longitude = HiddenField(id="lon")


class ClockOutForm(FlaskForm):
    notes = TextAreaField('Enter Notes here')
    submit = SubmitField('Clock Out')
    latitude = HiddenField(id="lat")
    longitude = HiddenField(id="lon")