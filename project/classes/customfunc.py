from flask import request
from project.models import *
import socket
import re


# get ip address
def get_ip_address():
    ipaddress = 'UNKNOWN'
    if request.environ.get('HTTP_CLIENT_IP') is not None:
        ipaddress = request.environ['HTTP_CLIENT_IP']
    elif request.environ.get('HTTP_X_FORWARDED_FOR') is not None:
        ipaddress = request.environ['HTTP_X_FORWARDED_FOR']
    elif request.environ.get('HTTP_X_FORWARDED') is not None:
        ipaddress = request.environ['HTTP_X_FORWARDED']
    elif request.environ.get('HTTP_FORWARDED_FOR') is not None:
        ipaddress = request.environ['HTTP_FORWARDED_FOR']
    elif request.environ.get('HTTP_FORWARDED') is not None:
        ipaddress = request.environ['HTTP_FORWARDED']
    elif request.environ.get('REMOTE_ADDR') is not None:
        ipaddress = request.environ['REMOTE_ADDR']

    return ipaddress


# get host name by ip
def get_host_name_by_ip(ipaddress):
    return socket.gethostbyaddr(ipaddress)[0]


# Add Activity
def add_activity(eid, activity):
    user = Users.query.filter(Users.id == eid).first()
    if user is None:
        return False

    ipaddress = get_ip_address()
    hostname = ''
    try:
        hostname = get_host_name_by_ip(ipaddress)
    except Exception as e:
        hostname = get_ip_address()

    log = Logs()
    log.eid = eid
    log.computer_name = hostname
    log.activity = activity
    log.date = datetime.utcnow()
    try:
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print("add activity error", e)
        return False
    return True


# Add Activity with hostname
def add_activity_hostname(eid, activity, hostname):
    user = Users.query.filter(Users.id == eid).first()
    if user is None:
        return False

    log = Logs()
    log.eid = eid
    log.computer_name = hostname
    log.activity = activity
    log.date = datetime.utcnow()
    try:
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print("add activity error", e)
        return False
    return True


# check email address valid
def is_valid_email(email):
    if len(email) > 7:
        if re.match('[^@]+@[^@]+\.[^@]+', email) is not None:
            return True
    return False
