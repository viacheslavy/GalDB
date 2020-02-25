#!/usr/bin/env python

import os.path
import os
from flask import Flask, request, render_template, url_for, json, redirect, g, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    current_user,
    LoginManager,
    login_required,
    login_user,
    logout_user
)
from project import config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "%s://%s:%s@%s/%s" % (
    config.DBTYPE, config.DBUSER, config.DBPASS, config.DBHOST, config.DBNAME)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = config.SECRET_KEY
db = SQLAlchemy(app)


# start the login system
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


from project.models import *
from project.controllers import aminos
from project.controllers import designs
from project.controllers import recipe
from project.controllers import maldi_recipe
from project.controllers import asynctask
from project.controllers import users
from project.controllers import login
from project.controllers import logs
from project.apis import recipe_api


@app.teardown_request
def shutdown_session(exception=None):
    db.session.remove()


@login_manager.user_loader
def user_loader(id):
    return Users.query.get(int(id))


@app.before_request
def before_request():
    g.user = current_user


# Override function url_for
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename and (filename.endswith('style.css') or filename.endswith('custom.js')):
            file_path = os.path.join(app.root_path, endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


# Error Pages
@app.errorhandler(500)
def error_page(e):
    print('error_page:', e)
    return render_template('error_pages/500.html'), 500


@app.errorhandler(404)
def not_found(e):
    print('not_found:', e)
    return render_template('error_pages/404.html'), 404


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('error_pages/403.html'), 403


# login view
@app.route('/login', methods=['GET'])
@app.route("/")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('recipe'))
    return render_template('login.html')





