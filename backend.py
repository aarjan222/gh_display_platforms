import plotly.io as pio
import plotly.express as px
from flask import Flask, render_template, redirect, request, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import boto3
import pandas as pd

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

db = SQLAlchemy(app)


class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(100))

    def __init__(self, name):
        self.name = name


@app.route('/')
@app.route('/home')
def home():
    return render_template("index.html")


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        session.permanent = True
        user = request.form['nm']
        session['user'] = user
        flash(f"Login Successful, {user}", "info")

        usr = users(user)
        db.session.add(usr)
        db.session.commit()

        return redirect(url_for("user"))
    else:
        if "user" in session:
            # TODO: to switch login user instead of redirecting to user and login page
            flash(f"Already Logged in by, {session['user']}", "info")
            return redirect(url_for("user"))
        flash(f"Create Account first", "info")

        return render_template("login.html")


@app.route('/user')
def user():
    if "user" in session:
        print("logged in")
        user = session['user']
        flash(f'Current User {user}')
        return render_template("user.html", user=user)
    else:
        flash(f"No user, first login", "info")

        return redirect(url_for("login"))


@app.route('/logout')
def logout():
    if "user" in session:
        user = session['user']
        session.pop("user", None)
        flash(f"You have been logged out, {user}!", "info")

    return redirect(url_for("login"))


@app.route('/monitor')
def monitor():
    if 'user' in session:
        param1 = request.args.get('param1')

        # -----------------------Do Only Once when needed-----------------------------------------------
        # uploading datas to s3 buckets
        # s3.Bucket('s3-to-local').upload_file(
        #     Filename='/home/aarjan/pajor_mroject/flask/gh_display_platforms/static/images/gh.jpg', Key='gh.jpg')

        # downloading datas from s3 buckets
        # s3.Bucket(
        #     's3-to-local').download_file(Key='crop_data.csv', Filename='crop_data.csv')
        # ----------------------------------------------------------------------------------------------

        greenhouse_data = pd.read_csv('crop_data.csv')

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
        flash(f'First create account using login page')
        return render_template('login.html')


@app.route('/control')
def control():
    return render_template('control.html')


@app.route('/view')
def view():
    if 'user' in session:
        user = session.get('user')
        if user == "admin":
            return render_template("view.html", values=users.query.all())
        else:
            print('only admin can view this page')
            flash(f'Cant view users information, login as admin account')
            return redirect(url_for("user"))
    else:
        return redirect(url_for('login'))


@app.route('/del/<usr>')
def delete(usr):
    users.query.filter_by(name=usr).delete()
    db.session.commit()
    flash(f'{usr} is deleted successfully!')
    return redirect(url_for("view"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
