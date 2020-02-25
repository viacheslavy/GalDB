# DesignDB #

DesignDB is a database management system for GalDB

## Install ##

    pip install -r requirements.txt

## Customize and Configure ##

Customize and configure your project by replacing `project` in several files including:

runserver.py

wsgi.py

models.py

project/

project/views.py

## Run ##

    python runserver.py


## Database Migration ##

    python manage.py db init
    python manage.py db migrate
    python manage.py db upgrade