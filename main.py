"""`main` is the top level module for your Flask application."""

# Import the Flask Framework
from flask import render_template, url_for, redirect, abort, request
from application import app
from flask_security import login_required, Security, current_user
from flask_security_ndb import send_email, NDBUserDatastore, User, Role
from admin import admin_app, add_default_views
#from security import security_app
from google.appengine.ext import ndb
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from flask_nav import Nav
from markupsafe import escape
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
import datetime

import timesheet
nav = Nav()
nav.init_app(app)

#security_app.init_app(app)
# Override Flask-Mail for Google App Engine by using the hook in :class:`flask_security.core._SecurityState`
user_datastore = NDBUserDatastore(User, Role)
security = Security(app, user_datastore)

security.send_mail_task(send_email)

admin_app.init_app(app)
#timesheet_app.init_app(app)
add_default_views(admin_app)

nav.register_element('console', Navbar(
    View('Dashboard', 'timesheet.view'),
    View('Hours History', 'timesheet.history'),
    View('Logout', 'security.logout')
))
nav.register_element('admin_console', Navbar(
    View('Admin Console', 'admin.index'),
    View('Dashboard', 'timesheet.admin_dashboard'),
    View('Logout', 'security.logout')
))
nav.register_element('login', Navbar(
    View('Login', 'security.login'),
    View('Register', 'security.register')
))

# Create a user to test with
@app.before_first_request
def create_user():
    #datastore = NDBDatastore(security_app.datastore, security_app.datastore.UserDatastore)
    datastore = user_datastore
    #datastore = security_app.datastore
    role = datastore.find_or_create_role(name='admin', description='Admin role')
    role2 = datastore.find_or_create_role(name='employee', description='Employee role')

    user = datastore.create_user(email='admin@novautobody.com', password='pabalma11', first_name='Myung', last_name='Lee', last_login_ip=request.remote_addr)
    datastore.get_user('admin@novautobody.com').confirmed_at = datetime.datetime.now()
    datastore.add_role_to_user(user, role2)
    datastore.add_role_to_user(user, role)

    user2 = datastore.create_user(email='seana@novautobody.com', password='nova8400', first_name='Seana', last_name='', last_login_ip=request.remote_addr)
    datastore.get_user('seana@novautobody.com').confirmed_at = datetime.datetime.now()
    datastore.add_role_to_user(user2, role2)

    user3 = datastore.create_user(email='adrianna@novautobody.com', password='nova8400', first_name='Adrianna', last_name='', last_login_ip=request.remote_addr)
    datastore.get_user('adrianna@novautobody.com').confirmed_at = datetime.datetime.now()
    datastore.add_role_to_user(user3, role2)

@app.route('/static/admin/<path:filename>')
@login_required
def static_admin_routes(filename):
    print(filename)
    return abort(404)

@app.route('/')
@login_required
def home():
    """Return a friendly homepage."""
    current_user.last_login_ip = request.remote_addr
    current_user.put()
    if current_user.has_role('admin'):
        return redirect(url_for('timesheet.admin_dashboard'))
    return redirect(url_for('timesheet.view'))

@app.route('/user', methods=['GET'])
@login_required
def user():
    user = {
            'first_name': current_user.first_name.title(),
            'last_name': current_user.last_name.title(),
            'id': current_user.id
            }
    return jsonify(user)

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500

@app.errorhandler(401)
def unauthorized_error(e):
    return 'Sorry, unauthorized access', 401

@app.errorhandler(403)
def forbidden_error(e):
    return 'Forbidden access', 403
