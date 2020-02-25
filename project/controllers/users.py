from flask import render_template, json, request

from project.views import app, login_required
from project import config
from project.models import *
from sqlalchemy import func
from email.mime.text import MIMEText
from project.classes import customfunc
from urllib.parse import urlparse
import hashlib
import smtplib
import random
import string


# render users template
@app.route("/users", methods=['GET'])
@login_required
def users():
    userroles = db.session.query(UserRole.roleid, UserRole.rolename).all()
    return render_template('users.html', menu='users', userroles=userroles)


# render logged in users template
@app.route("/logged_in_users", methods=['GET'])
@login_required
def logged_in_users():
    return render_template('logged_in_users.html', menu='loggedin_users')


# add user
@app.route("/add_user", methods=['POST'])
@login_required
def add_user():
    result = {'result': 'ERROR', 'msg': ''}

    username = request.form['username']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    role = request.form['role']
    amino_editor = request.form['amino_editor']
    design_editor = request.form['design_editor']
    recipe_editor = request.form['recipe_editor']

    user = Users.query.filter(func.lower(Users.username) == func.lower(username)).first()
    if user is not None:
        result['msg'] = 'Duplicate: The user already exist'
        return json.dumps(result)

    new_password = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(12))
    password = hashlib.md5(new_password.encode("utf8")).hexdigest()

    user = Users()
    user.username = username
    user.password = password
    user.firstname = firstname
    user.lastname = lastname
    user.email = email
    user.role = role
    if user.role == 2:
        user.amino_editor = -1
        user.design_editor = -1
        user.recipe_editor = -1
    else:
        user.amino_editor = amino_editor
        user.design_editor = design_editor
        user.recipe_editor = recipe_editor

    try:
        db.session.add(user)
        db.session.commit()

        server = smtplib.SMTP(config.MAIL_SERVER_HOST)
        server.login(config.MAIL_SERVER_USERNAME, config.MAIL_SERVER_PASSWORD)

        body_text = "Hello " + user.firstname + ",\n\n"
        body_text += "You have been granted access to DesignDB.\n\n"
        body_text += "If you did not make this request please notify your Administrator!\n\n"
        body_text += "Username:        " + user.username + "\n"
        body_text += "Password:    " + new_password + "\n\n"
        body_text += "Sign in URL:     " + request.host_url + "\n\n"
        body_text += "DESIGN DB" + "\n"
        body_text += "System Administration" + "\n"
        msg = MIMEText(body_text)
        msg['Subject'] = 'DesignDB Notification'
        msg['From'] = 'Design Db - NO Reply<designdb@healthtell.io>'
        msg['To'] = user.email

        server.send_message(msg)

        result['id'] = user.id
        result['result'] = 'SUCCESS'
    except Exception as e:
        print("add new user error:", e)
        result['msg'] = str(e)

    return json.dumps(result)


# edit user
@app.route("/edit_user", methods=['POST'])
@login_required
def edit_user():
    result = {'result': 'ERROR', 'msg': ''}
    userid = request.form['userid']
    username = request.form['username']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    role = request.form['role']
    amino_editor = request.form['amino_editor']
    design_editor = request.form['design_editor']
    recipe_editor = request.form['recipe_editor']

    user = Users.query.filter(Users.id == userid).first()
    if user is None:
        result['msg'] = 'User already exist.'
        return json.dumps(result)

    user = Users.query.filter(func.lower(Users.username) == func.lower(username)).first()
    if user is not None and user.id != int(userid):
        result['msg'] = 'Username already exist.'
        return json.dumps(result)

    user = Users.query.filter(Users.id == userid).first()
    user.username = username
    user.firstname = firstname
    user.lastname = lastname
    user.email = email
    user.role = role
    if user.role == 2:
        user.amino_editor = -1
        user.design_editor = -1
        user.recipe_editor = -1
    else:
        user.amino_editor = amino_editor
        user.design_editor = design_editor
        user.recipe_editor = recipe_editor

    db.session.commit()
    result['result'] = 'SUCCESS'
    result['msg'] = ''
    return json.dumps(result)


# get users
@app.route("/get_users", methods=['POST'])
@login_required
def get_users():
    result = {'result': 'ERROR', 'msg': '', 'data': []}

    users = db.session.query(Users.id, Users.username, Users.firstname, Users.lastname, Users.email, UserRole.roleid, UserRole.rolename, Users.amino_editor, Users.design_editor, Users.recipe_editor).outerjoin(UserRole, UserRole.roleid == Users.role).order_by(Users.username).all()

    if users is not None:
        result['result'] = 'SUCCESS'
        for user in users:
            amino_editor = user.amino_editor
            if amino_editor is None:
                amino_editor = 0
            design_editor = user.design_editor
            if design_editor is None:
                design_editor = 0
            recipe_editor = user.recipe_editor
            if recipe_editor is None:
                recipe_editor = 0
            json_obj = {
                "id": user.id,
                "username": user.username,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "email": user.email,
                "roleid": user.roleid,
                "rolename": user.rolename,
                "amino_editor": amino_editor,
                "design_editor": design_editor,
                "recipe_editor": recipe_editor
            }
            result['data'].append(json_obj)

    return json.dumps(result)


# get users
@app.route("/get_loggedin_users", methods=['POST'])
@login_required
def get_loggedin_users():
    result = {'result': 'ERROR', 'msg': '', 'data': []}

    users = db.session.query(Users.id, Users.username, Users.last_login, Users.computer_name, Users.last_request).order_by(Users.username).all()

    if users is not None:
        result['result'] = 'SUCCESS'
        for user in users:
            tmp1 = user.last_request
            tmp2 = datetime.utcnow()
            if tmp1 is None:
                continue

            if (tmp2-tmp1).total_seconds() > 60:
                continue

            json_obj = {
                "id": user.id,
                "username": user.username,
                "last_login": user.last_login,
                "computer_name": user.computer_name
            }
            result['data'].append(json_obj)

    return json.dumps(result)


# do reset password and send email
def do_reset_password_send_email(username):
    result = {'result': 'ERROR'}
    new_password = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(12))
    user = Users.query.filter(func.lower(Users.username) == func.lower(username)).first()
    if user is not None:
        if user.email is None or len(user.email) == 0 or customfunc.is_valid_email(user.email) is False:
            result['msg'] = 'Email is invalid'
            return result

        tmp2 = hashlib.md5(new_password.encode("utf8")).hexdigest()
        user.password = tmp2
        db.session.commit()

        server = smtplib.SMTP(config.MAIL_SERVER_HOST)
        server.login(config.MAIL_SERVER_USERNAME, config.MAIL_SERVER_PASSWORD)

        body_text = "Hello " + user.firstname + ",\n\n"
        body_text += "Your password has been reset for Design DB.\n\n"
        body_text += "If you did not make this request please notify your Administrator!\n\n"
        body_text += "Username:        " + user.username + "\n"
        body_text += "New Password:    " + new_password + "\n\n"
        body_text += "Sign in URL:     " + request.host_url + "\n\n"
        body_text += "Design DB" + "\n"
        body_text += "System Administration" + "\n"
        msg = MIMEText(body_text)
        msg['Subject'] = 'Design DB Notification'
        msg['From'] = "Design Db - NO Reply<designdb@healthtell.io>"
        msg['To'] = user.email
        server.send_message(msg)
        result['result'] = 'SUCCESS'

    return result


# Reset new password and send email to the user.
@app.route("/reset_password_send_email", methods=['POST'])
def reset_password_send_email():
    username = request.form['username']
    result = do_reset_password_send_email(username)
    return json.dumps(result)
