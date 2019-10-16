from flask import render_template, flash, redirect, url_for, request
from app.models import User, Timesheet, CostCenter, Role
from app import app, db
from app.forms import LoginForm, RegistrationForm, ClockInForm, ClockOutForm, SelectEmployeeForm
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
        if is_admin() is False:
            return redirect(url_for('clockin'))
        else:
            return redirect(url_for('selectemployee'))
    print("current_user is auth:" + str(current_user.is_authenticated))
    return render_template('login.html', title='Sign In', form=form,auth=current_user.is_authenticated)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if is_admin():
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data, realname=form.realname.data,usertype=2)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('User Successfully registered')
            return redirect(url_for('register'))
    else:
        return redirect('login')
    return render_template('register.html', title='Register', form=form)

@app.route('/clockin', methods=['GET','POST'])
@login_required
def clockin():
    tcit = getTotalClockedInTime(current_user.id)
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
        loc = str(form.latitude.data) + "," + str(form.longitude.data)
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
        loc = str(form.latitude.data) + "," + str(form.longitude.data)
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

def getTotalClockedInTime(id):
    totalClockedInTime = 0
    today = date.today()
    idx = (today.weekday() + 1) % 7
    saturday = today - timedelta(1 + idx)
    friday = today + timedelta(5 + idx)
    print(saturday)
    print(friday)
    q = Timesheet.query.filter(Timesheet.starttime.between(saturday,friday), Timesheet.employee == id).all()
    for row in q:
        if row.totaltime is not None:
            totalClockedInTime += int(row.totaltime)
    return totalClockedInTime

@app.route('/admin', methods = ['GET','POST'])
def admin():
    if is_admin():
        return render_template("admin.html", title="Administrator", user = current_user)
    else:
        return redirect(url_for('index'))

@app.route('/employee/<employee>', methods=['GET','POST'])
@login_required
def employee(employee):
    today = date.today()
    idx = (today.weekday() + 1) % 7
    saturday = today - timedelta(1 + idx)
    friday = today + timedelta(5 + idx)
    q = Timesheet.query.filter(Timesheet.starttime.between(saturday, friday),
                               Timesheet.employee == employee).all()
    e = User.query.filter_by(id = employee).first()
    costcenterchoices = [(c.name) for c in CostCenter.query.all()]
    tcit = getTotalClockedInTime(employee)
    hoursClockedIn = floor(int(tcit) / 60)
    minutesClockedIn = int(tcit) % 60
    return render_template("showtime.html", title="Employee Clock In Details", data = q, employee = e,
                           costcenter=costcenterchoices,
                           clockedintime = str(hoursClockedIn) + ":" + str(minutesClockedIn).zfill(2))

@app.route('/selectemployee',methods = ['GET','POST'])
@login_required
def selectemployee():
    form = SelectEmployeeForm()
    if is_admin():
        if form.validate_on_submit():
            employeeid = form.employee.data
            return redirect('/employee/' + str(employeeid))
        return render_template("selectemployee.html", title="Get Employee Details", form=form)
    return

@app.route('/initialsetup')
def initialsetup():
    users = User.query.first()
    print(users)
    if users is None:
        print("setting up users")
        user = User(username='admin', email='essary@gmail.com', realname='Michael Essary', usertype=1)
        user.set_password("pyctswap2")
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('admin'))
    else:
        print("didnt do shit")
    return redirect(url_for('login'))

def is_admin():
    admin = User.query.filter(and_(User.id == current_user.id, User.usertype == '1')).first()
    if admin is not None:
        return True
    else:
        return False