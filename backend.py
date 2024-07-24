from flask import Flask, render_template, redirect, request, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta


app = Flask(__name__)
app.secret_key = "helloworld"
app.permanent_session_lifetime = timedelta(minutes=2)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(100))

    def __init__(self, name):
        self.name = name


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


@app.route('/view')
def view():
    user = session.get('user')
    if user == "admin":
        return render_template("view.html", values=users.query.all())
    else:
        flash(f'Cant view users information, login as admin account')

        return redirect(url_for("user"))


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
