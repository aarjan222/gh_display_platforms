from flask import Flask, render_template, redirect, request, flash, session, url_for
from datetime import timedelta

import pandas as pd
import plotly.io as pio
import plotly.express as px

import boto3
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "helloworld"
app.permanent_session_lifetime = timedelta(minutes=2)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

s3 = boto3.resource(
    's3',
    region_name='us-east-1',
    aws_access_key_id='AKIA6ODU7PIYLXUTAPDL',
    aws_secret_access_key='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'
)

# Initialize the database
db = SQLAlchemy(app)
USERS = {}

with app.app_context():
    db.create_all()


class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(100))
    password = db.Column("password", db.String(100))

    def __init__(self, name, password):
        self.name = name
        self.password = password


@app.route('/')
@app.route('/home')
def home():
    return render_template("index.html")


@app.route('/register', methods=["POST", "GET"])
def register():
    # ---------------To clear all the Database--------------------------
    # users.__table__.drop(db.engine)
    # db.create_all()
    if request.method == "POST":
        name = request.form['nm']
        password = request.form['password']

        # check if this user already registered:
        if users.query.filter_by(name=name).first():
            flash(f"User already exists")
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = generate_password_hash(
            password, method='pbkdf2:sha256')
        new_user = users(name, hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user_name = request.form['nm']
        user_password = request.form['password']

        user = users.query.filter_by(name=user_name).first()

        if user and check_password_hash(user.password, user_password):
            session.permanent = True
            session['user'] = user_name
            flash(f"Login Successful, {user_name}", "info")

            return redirect(url_for('dashboard'))
        flash(f"Invalid Credentials!")
        return render_template('login.html')

    else:
        if "user" in session:
            flash(f"Already Logged in by, {session['user']}", "info")
            return redirect(url_for("dashboard"))

        # flash(f"Login first")
        return render_template("login.html")


@app.route('/dashboard')
def dashboard():
    if "user" in session:
        user_name = session['user']
        return render_template("dashboard.html", user=user_name)
    else:
        flash(f"First Login")
        return redirect(url_for("login"))


@app.route('/logout')
def logout():
    if "user" in session:
        user = session['user']
        session.pop("user", None)
        session.pop("password", None)
        flash(f"You have been logged out, {user}!", "info")
    flash(f"First Login")
    return redirect(url_for("login"))


@app.route('/monitor')
def monitor():
    if 'user' in session:
        param1 = session['user']
        print("current user = ", param1)

        # -----------------------Do Only Once when needed-----------------------------------------------
        # uploading datas to s3 buckets
        # s3.Bucket('s3-to-local').upload_file(
        #     Filename='/home/aarjan/pajor_mroject/flask/gh_display_platforms/static/images/gh.jpg', Key='gh.jpg')

        # downloading datas from s3 buckets
        # s3.Bucket(
        #     's3-to-local').download_file(Key='crop_data.csv', Filename='crop_data.csv')
        # ----------------------------------------------------------------------------------------------

        # ---------------------------------change the file location as your directory--------------------
        greenhouse_data = pd.read_csv(
            '~/pajor_mroject/flask/gh_display_platforms/crop_data.csv')

        # charts -> plotly figures -> html strings

        # Create Plotly figures for different charts
        fig_temp = px.line(greenhouse_data, x='Time',
                           y='Temperature', title='Temperature')
        fig_hum = px.line(greenhouse_data, x='Time',
                          y='Humidity', title='Humidity')

        # Convert Plotly figures to HTML strings
        temp_chart = pio.to_html(fig_temp, full_html=False)
        hum_chart = pio.to_html(fig_hum, full_html=False)

        return render_template('monitor.html', r=param1, data=greenhouse_data.to_dict(orient='records'),
                               temperature_chart=temp_chart, humidity_chart=hum_chart)
    else:
        flash(f"First Login")
        return redirect(url_for('login'))


@app.route('/control')
def control():
    # TODO
    if 'user' in session:
        param1 = session['user']
        return render_template('control.html', r=param1)


@app.route('/view')
def view():
    if 'user' in session:
        user = session.get('user')
        if user == "admin":
            return render_template("view.html", values=users.query.all())
        else:
            print('only admin can view this page')
            flash(f'Cant view users information, login as admin account')
            return redirect(url_for("dashboard"))
    else:
        flash(f"First Login")
        return redirect(url_for('login'))


@app.route('/del/<usr>')
def delete(usr):
    users.query.filter_by(name=usr).delete()
    db.session.commit()
    flash(f'{usr} is deleted successfully!')
    return redirect(url_for("view"))


if __name__ == "__main__":
    app.run(debug=True)
