from flask import Flask, request, render_template
import os
import dotenv
import pymysql
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import database


app = Flask(__name__, template_folder = 'templates')
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY')

database = database.Database()
database.setup_db()

# home page

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html', methods=['POST'])

@app.route('/notes')
def notes():
    return render_template('notes.html', methods=['POST'])

@app.route('/files')
def files():
    return render_template('files.html', methods=['POST'])

@app.route('/profile')
def profile():
    return render_template('profile.html', methods=['POST'])

@app.route('/signup')
def signup():
    return render_template('signup.html', methods=['POST'])

@app.route('/login')
def login():
    return render_template('login.html', methods=['POST'])



if __name__ == '__main__':
    app.run(debug=True)