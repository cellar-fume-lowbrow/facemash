#!flask/bin/python
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import configparser
import random
import os

app = Flask(__name__)
app.config.from_pyfile('config.py.sample')
db = SQLAlchemy(app)


class Subjects(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    upvotes = db.Column(db.Integer(), nullable=False, default=0)
    downvotes = db.Column(db.Integer(), nullable=False, default=0)
    elo_rank = db.Column(db.Float(), nullable=False, default=1200)

    def __init__(self, name: str):
        self.upvotes = 0
        self.downvotes = 0
        self.elo_rank = 1200
        self.name = name

    def __repr__(self):
        return '<Subject %r>' % self.id


K = 32


@app.route('/')
def home() -> render_template:
    """ Try to serve the main view if it fails due to ValueError catch it and serve a Too few contestants page instead
        Else show a generic error template with the exception printed out."""
    try:
        return render_template('index.html', contestants=random.sample(Subjects.query.all(), 2))
    except ValueError:
        return render_template('error.html', exception="Too few contestants in database to be able to start the game.")
    except Exception as excp:
        return render_template('error.html', exception=excp)


@app.route('/toplist')
def toplist() -> render_template:
    all_subjects = Subjects.query.order_by(Subjects.elo_rank.desc()).all()
    if len(all_subjects) > 1:
        return render_template('toplist.html', subjects=all_subjects)
    else:
        return render_template('error.html', exception="Not enough items to display the toplist")


@app.route('/upload')
def upload() -> render_template:
    """ Serve the upload page statically, this should not be able to fail. No try/catch needed for now."""
    return render_template('upload.html')


@app.route('/vote/<int:winner>/<int:loser>')
def vote(winner: int, loser: int) -> redirect:
    """ The function for the vote, modify the users elo_rank by the correct formulas.
        :returns a redirect"""
    # Fetch the winner and the loser from the database from the database by ID.
    winner: Subjects = Subjects.query.filter_by(id=winner).first()
    loser: Subjects = Subjects.query.filter_by(id=loser).first()

    winner.upvotes += 1
    loser.downvotes += 1

    ea: float = 1 / (1 + 10 ** ((loser.elo_rank - winner.elo_rank) / 400))
    eb: float = 1 / (1 + 10 ** ((winner.elo_rank - loser.elo_rank) / 400))

    winner.elo_rank = winner.elo_rank + (K * (1 - ea))
    loser.elo_rank = loser.elo_rank + (K * (0 - eb))

    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add_item', methods=['GET', 'POST'])
def upload_file() -> redirect:
    """Upload files to static/images and return a redirect """
    if request.method == 'POST':
        # Insert the image in the database.
        Project = request.form.get("Project")
        subject = Subjects(name=Project)
        db.session.add(subject)
        db.session.commit()

        return redirect(url_for('home'))
    else:
        return render_template('error.html', exception="Cannot access this page directly")
