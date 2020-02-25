from flask import render_template, request, json, session, Response, url_for
from project.models import *
from project.views import app, login_required, g


@app.route('/TaskStatus/<int:task_id>')
def task_status(task_id):
    result = {'task_id': task_id, 'status': '', 'info': ''}
    task = Tasks.query.filter(Tasks.id == task_id).first()
    if task is not None:
        result['status'] = task.status
        result['info'] = task.info

    return json.dumps(result)


# generate new task
def new_task():
    task = Tasks()
    task.status = 'Processing'
    task.info = '0'
    db.session.add(task)
    db.session.commit()

    return task.id
