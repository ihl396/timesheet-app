# -*- coding: utf-8 -*-
"""
.. module:: application
    :synopsis: Module with no side effects to import the main Flask application object
"""
from flask import Flask
from flask_bootstrap import Bootstrap
import pytz
from datetime import datetime

app = Flask(__name__, instance_relative_config=True)
Bootstrap(app)
app.config.from_object('config.AppSettings')

from timesheet.views import timesheet_bp
app.register_blueprint(timesheet_bp, url_prefix='/timesheet')

def do_urlescape(value):
    """Escape for use in URLs."""
    return urllib.quote(value.encode('utf8'))
app.jinja_env.globals['urlencode'] = do_urlescape
"""
local_time = pytz.timezone("US/Eastern")
time = datetime.utcnow().replace(microsecond=0).replace(tzinfo=pytz.utc)
time = time.astimezone(local_time)
"""

#from . import timesheet
#timesheet_app.init_app(app)
#app.register_blueprint(timesheet, url_prefix='/timesheet')

