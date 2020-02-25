#!/usr/bin/env python

import configparser
import os.path

config = configparser.ConfigParser()
filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
config.read(filename)

# API token
API_TOKEN = os.getenv("api_token", config.get('app', 'APITOKEN'))

# Read config.ini and store into variables
HOST = config.get('app', 'HOST')
PORT = int(config.get('app', 'PORT'))
DEBUG = config.get('app', 'DEBUG')
SECRET_KEY = config.get('app', 'SECRETKEY')

DBTYPE = config.get('database', 'DBTYPE')
DBHOST = os.getenv("db_host", config.get('database', 'DBHOST'))
DBNAME = os.getenv("db_name", config.get('database', 'DBNAME'))
DBUSER = os.getenv("db_user", config.get('database', 'DBUSER'))
DBPASS = os.getenv("db_pass", config.get('database', 'DBPASS'))

MAIL_SERVER_HOST = "smtp.mailgun.org"
MAIL_SERVER_USERNAME = "waferdb@healthtell.io"
MAIL_SERVER_PASSWORD = "Chandler_499_Sanramon_!"

