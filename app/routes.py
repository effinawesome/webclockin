from flask import render_template, flash, redirect, url_for, request
from app.models import User, Timesheet, CostCenter, Role
from app import app, db
from app.forms import LoginForm, RegistrationForm, ClockInForm, ClockOutForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime, date, timedelta
from math import floor
from sqlalchemy import and_, func
loc = ""

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Title', user = current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('clockin'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user,remember=form.remember_me.data)
        return redirect(url_for('clockin'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('clockin'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/clockin', methods=['GET','POST'])
@login_required
def clockin():

    tcit = getTotalClockedInTime()
    hoursClockedIn = floor(int(tcit) / 60)
    minutesClockedIn = int(tcit) % 60
    clocked = Timesheet.query.filter(Timesheet.employee == current_user.id, Timesheet.clockedin == '1').first()
    timesheet = Timesheet()
    print("current_user.id: " + str(current_user.id))
    print("clocked ( clock in) :" + str(clocked))
    if clocked is not None:
        return redirect(url_for('clockout'))
    form = ClockInForm()
    if form.validate_on_submit():
        loc = str(form.latitude.data) + " " + str(form.longitude.data)
        print("location from clock in(a): " + loc)
        #clocked = timesheet.query.filter(Timesheet.employee == current_user.id, Timesheet.clockedin == '1').first()
        #print(clocked)
        #if clocked is None:
        timesheet.employee = current_user.id
        timesheet.starttime = datetime.now().replace(microsecond=0)
        timesheet.clockedin = 1
        timesheet.inlocation = loc
        timesheet.costcenter = form.jobname.data
        db.session.add(timesheet)
        db.session.commit()
        return redirect(url_for('clockout'))
    return render_template('clockin.html',title='Clock In',form=form, clockedintime=str(hoursClockedIn) + " hours and " + str(minutesClockedIn) + " minutes")

@app.route('/clockout', methods=['GET','POST'])
@login_required
def clockout():
    #timesheet = Timesheet()
    form = ClockOutForm()
    clocked = Timesheet.query.filter(and_(Timesheet.employee == current_user.id, Timesheet.clockedin == '1')).first()
    print("current_user.id: " + str(current_user.id))
    print("clocked ( clock out) :" + str(clocked))
    if clocked is None:
        return redirect(url_for('clockin'))
    if form.validate_on_submit():
        loc = str(form.latitude.data) + " " + str(form.longitude.data)
        if clocked is not None:
            clocked.employee = current_user.id
            end = datetime.now().replace(microsecond=0)
            clocked.endtime = end
            clocked.outlocation = loc
            clocked.notes = form.notes.data
            td = end - clocked.starttime
            hours = td.seconds / 3600
            minutes = td.seconds % 3600 / 60
            clocked.totaltime = str(round(hours*60+minutes))
            print(form.notes.data)
            clocked.clockedin = 0
            db.session.add(clocked)
            db.session.commit()
            return redirect(url_for('clockin'))
        else:
            return redirect(url_for('clockout'))

    return render_template('clockout.html', title='Clock Out', form=form)

@app.route('/clockinBGprocess', methods = ['POST'])
def clockinBGprocess():
    loc = str(request.get_data()).strip("'b")
    print("location from clock in bg: " + loc)
    return redirect(url_for('clockout'))

def getTotalClockedInTime():
    totalClockedInTime = 0
    today = date.today()
    idx = (today.weekday() + 1) % 7
    saturday = today - timedelta(1 + idx)
    friday = today + timedelta(5 + idx)
    print(saturday)
    print(friday)
    q = Timesheet.query.filter(Timesheet.starttime.between(saturday,friday), Timesheet.employee == current_user.id).all()
    for row in q:
        if row.totaltime is not None:
            totalClockedInTime += int(row.totaltime)
    return totalClockedInTime

@app.route('/admin', methods = ['GET','POST'])
def admin():
    admin = User.query.filter(and_(User.id == current_user.id, User.usertype == '1')).first()
    if admin is not None:
        return render_template("admin.html", title="Administrator", user = current_user, data=data)
    else:
        return redirect(url_for('index'))