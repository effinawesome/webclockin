from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), index = True, unique = True)
    realname = db.Column(db.String(128))
    email = db.Column(db.String(128),unique=True)
    password_hash = db.Column(db.String(128))
    usertype = db.Column(db.Integer, db.ForeignKey('role.id'))

    def __repr__(self):
        return '{}'.format(self.realname)

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
       return check_password_hash(self.password_hash, password)

    def check_admin(type):
        return type is '1'

class Role(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    role = db.Column(db.String(255))

class CostCenter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

class Timesheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.String, index=True, default=date.today().strftime('%m-%d-%y'))
    starttime = db.Column(db.DateTime)
    endtime = db.Column(db.DateTime)
    totaltime = db.Column(db.String)
    inlocation = db.Column(db.String(255))
    outlocation = db.Column(db.String(255))
    notes = db.Column(db.String(1024))
    clockedin = db.Column(db.Boolean)
    costcenter = db.Column(db.Integer, db.ForeignKey('cost_center.id'))



@login.user_loader
def load_user(id):
    return User.query.get(int(id))