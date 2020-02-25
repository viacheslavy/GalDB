#!/usr/bin/env python
from flask import render_template, request, json
from project.views import app, login_required, g
from project.models import *
from sqlalchemy import exc, func, or_


@app.route("/logs", methods=['GET'])
@login_required
def logs():
    users = Users.query.order_by(Users.username).all()
    computers = db.session.query(Logs.computer_name).group_by(Logs.computer_name).order_by(Logs.computer_name.asc()).all()
    return render_template('logs.html', menu="logs", users=users, computers=computers)


# get logs
@app.route("/get_logs", methods=['POST'])
@login_required
def get_logs():
    result = {'result': 'ERROR', 'msg': '', 'data': []}
    username = request.form['username']
    computer = request.form['computer']
    activity = request.form['activity']
    date_start = request.form['date_start']
    date_end = request.form['date_end']
    print(date_end)

    query = db.session.query(Logs.id, Logs.eid, Users.username, Logs.computer_name, Logs.activity, Logs.date).outerjoin(Users, Users.id == Logs.eid)
    if username != '0':
        query = query.filter(Logs.eid == int(username))
    query = query.filter(Logs.computer_name.like("%" + computer + "%"), Logs.activity.like("%" + activity + "%"))

    if date_start != '':
        query = query.filter(Logs.date >= date_start)
    if date_end != '':
        query = query.filter(Logs.date < date_end)

    logs = query.order_by(Logs.date.desc()).limit(500).all()
    if logs is not None:
        result['result'] = 'SUCCESS'
        for log in logs:
            json_obj = {
                "id": log.id,
                "username": log.username,
                "computer_name": log.computer_name,
                "activity": log.activity,
                "date": log.date
            }
            result['data'].append(json_obj)

    return json.dumps(result)
