#!/usr/bin/env python

from project import views
from project import config
from project.controllers import service


app = views.app

# Return an App
if __name__ == "__main__":
    service.init_db()
    service.start_service()
    views.app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, use_reloader=False)
