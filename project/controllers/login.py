from flask import request, json, redirect, url_for, session
from project.views import app, db, login_user, current_user, logout_user, login_required,g
from project.models import *
from sqlalchemy import func
from urllib.parse import urlparse
from project.controllers.asynctask import new_task
import hashlib
import socket
import threading


# verify user credential
@app.route('/validate_user', methods=['POST'])
def validate_user():
    result = {'result': 'ERROR', 'error': 0}

    if request.method == 'POST':
        username = str(request.form['username'])
        password = str(request.form['password'])

        password = hashlib.md5(password.encode("utf8")).hexdigest()

        filtered_user = Users.query.filter(func.lower(Users.username) == func.lower(username)).first()
        if filtered_user is None:
            result['error'] = 1
            return json.dumps(result)
        else:
            if filtered_user.password != password:
                result['error'] = 2
                return json.dumps(result)
            user = filtered_user

        user.last_login = datetime.utcnow()
        user.last_request = datetime.utcnow()

        try:
            user.computer_name = socket.getfqdn(request.remote_addr)
        except Exception as e:
            print("Get host name by ip error=", e)

        db.session.commit()
        login_user(user, remember=True)
        result['result'] = 'SUCCESS'
        return json.dumps(result)
    else:
        return json.dumps(result)


# logout user
@app.route("/logout", methods=['GET'])
@login_required
def logout():
    if current_user.is_authenticated:
        g.user.created_recipes = ''
        g.user.last_request = None
        db.session.commit()

        logout_user()
        session.pop("current_recipe_id", None)
        session.pop("current_design_id", None)
    return redirect(url_for('login'))


# Frequently set last_access time to current user.
@app.route("/send_last_request", methods=['POST'])
@login_required
def send_last_request():
    try:
        if hasattr(g.user, 'username'):
            user = Users.query.filter(func.lower(Users.username) == func.lower(g.user.username)).first()
            if user is not None and user.is_authenticated():
                user.last_request = datetime.utcnow()
                db.session.commit()
    except Exception as e:
        print("send_last_request error=", e)
    return 'success'
