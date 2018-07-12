from flask_security import login_required, current_user
from flask import Blueprint, current_app, redirect, render_template, request, \
    session, url_for, jsonify, flash, abort
from flask_wtf import FlaskForm as Form
from flask_admin import BaseView, expose
from wtforms.fields.html5 import DateField
from flask_security_ndb import NDBClock_Type, NDBTimesheet, User, \
        Role, Log, Clock_Type, NDBUserDatastore
from datetime import datetime, tzinfo, timedelta
import time
import json
import pytz
from dateutil import parser
from functools import wraps

timesheet_bp = Blueprint('timesheet', __name__)

def utc2local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
   # print((utc+offset).strftime('%m-%d-%y %I:%M %p'))
    return utc+offset

def is_accessible(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.has_role('admin'):
            return f(*args, **kwargs)
        return abort(403)
    return decorated_function

@is_accessible
class AdminView(BaseView):

    @timesheet_bp.route('/admin', methods=['GET'])
    @login_required
    @is_accessible
    def admin_dashboard():
        form = DateForm()
        return render_template("timesheet/admin.html", form=form)

    @timesheet_bp.route('/users', methods=['GET'])
    @login_required
    @is_accessible
    def get_users():
        user = NDBUserDatastore(User, Role)
        users_raw = user.get_users()
        users = [{ 'id': x.id, 
                     'first_name': x.first_name,
                     'last_name': x.last_name,
                     'last_login_ip': x.last_login_ip,
                     'clocked_in': x.clocked_in
                 }
                for x in users_raw
               ]
        for x in users:
            x['roles'] = [{ 'role': y.id() }
                    for y in user.get_user(x['id']).roles_
                    ]
        return jsonify(users)

    @timesheet_bp.route('/history/<id>/get_hours', methods=['POST'])
    @login_required
    @is_accessible
    def get_hours_by_id(id):
        log = NDBTimesheet(Log)
        users = NDBUserDatastore(User, Role)
        user = users.get_user(id)
        try:
            form = DateForm()
            data = json.loads(request.data.decode())
        except TypeError:
            return jsonify({"worked": None})
        try:
            startDate = parser.parse(data['startDate'])
            endDate = parser.parse(data['endDate'])
        except KeyError:
            return jsonify({"worked": None})
        # weird timezone bug
        startDate = startDate.replace(hour=0, minute=0)
        endDate = endDate.replace(hour=23, minute=59, second=59)
        log_entries = log.get_entries(user=user, startDate=startDate, endDate=endDate)
        difference = [y.timestamp-x.timestamp for x, y in zip(log_entries[0::2], log_entries[1::2])]
        worked = sum(difference, timedelta())
        hours = worked.total_seconds()/3600
        return jsonify({"worked": "{0:.2f}".format(hours)})

    @timesheet_bp.route('/view/entries', methods=['POST'])
    @login_required
    @is_accessible
    def get_entries_by_id():
        log = NDBTimesheet(Log)
        users = NDBUserDatastore(User, Role)
        try:
            data = json.loads(request.data.decode())
        except TypeError:
            return jsonify(None)
        try:
            startDate = parser.parse(data['startDate'])
            endDate = parser.parse(data['endDate'])
            user = users.get_user(data['user'])
        except KeyError:
            return jsonify(None)
        # weird timezone bug
        startDate = startDate.replace(hour=0, minute=0)
        endDate = endDate.replace(hour=23, minute=59, second=59)
        log_entries_raw = log.get_entries(user=user, startDate=startDate, endDate=endDate)
        log_entries = [{'entry_id': x.id, 'timestamp': x.timestamp.strftime("%m-%d-%y %I:%M %p"),
                        'clock_type': x.clock_type.id(), 'editing': False}
                            for x in log_entries_raw]
        return jsonify(log_entries)


    @timesheet_bp.route('/entry/add', methods=['POST'])
    @login_required
    @is_accessible
    def add_log_entry():
        user = NDBUserDatastore(User, Role)
        log = NDBTimesheet(Log)
        clock_types = NDBClock_Type(Clock_Type)
        form = DateForm()

        data = json.loads(request.data.decode())
        try:
            user = user.get_user(data['user'])
            timestamp = parser.parse(data['timestamp'])
            clock_type = data['clock_type']
        except KeyError:
            flash(u'Please select date and time', 'error')
        clock = clock_types.get_or_create_type(text=clock_type)
        x = log.create_entry(user=user.key, timestamp=timestamp, clock_type=clock.key)
        log_entry = {'timestamp': x.timestamp.strftime("%m-%d-%y %I:%M %p"), 'clock_type': x.clock_type.id()}
        
        return jsonify(log_entry)

    @timesheet_bp.route('/clock_types', methods=['GET'])
    @login_required
    @is_accessible
    def get_clock_types():
        clock_types = NDBClock_Type(Clock_Type)
        clock_types_raw = clock_types.get_all()
        clock_types = [{'clock_type': x.id}
                            for x in clock_types_raw]
        return jsonify(clock_types)

    @timesheet_bp.route('/entry/delete', methods=['POST'])
    @login_required
    @is_accessible
    def remove_log_entry():
        timesheet = NDBTimesheet(Log)
        try:
            data = json.loads(request.data.decode())
        except TypeError:
            return jsonify({'success': False})
        try:
            entry_id = data['entry_id']
        except KeyError:
            return jsonify({'success': False})
        success = timesheet.delete_entry_by_id(entry_id)
        return jsonify({'success': True})

    @timesheet_bp.route('/entry/edit', methods=['POST'])
    @login_required
    @is_accessible
    def edit_log_entry():
        clock_types = NDBClock_Type(Clock_Type)
        timesheet = NDBTimesheet(Log)
        try:
            data = json.loads(request.data.decode())
        except TypeError:
            return jsonify({'success': False})
        try:
            timestamp = parser.parse(data['timestamp'])
            clock_type = clock_types.get_type(data['clock_type'])
            entry_id = data['entry_id']
        except KeyError:
            return jsonify({'success': False})
        log = timesheet.get_entry(entry_id)
        log.timestamp = timestamp
        log.clock_type = clock_type.key
        log.put()
        entry = [{'timestamp': log.timestamp, 'clock_type': log.clock_type.id(), 'entry_id': log.id}]
        return jsonify(entry)


@timesheet_bp.route('/', methods=['GET'])
@login_required
def view():
    return render_template("timesheet/index.html")

@timesheet_bp.route('/entries', methods=['POST'])
@login_required
def current_user_entries():
    log = NDBTimesheet(Log)
    user = current_user
    try:
        data = json.loads(request.data.decode())
    except TypeError:
        return jsonify({'log_entries': None})
    try:
        startDate = parser.parse(data['startDate'])
        endDate = parser.parse(data['endDate'])
    except KeyError:
        return jsonify({'log_entries': None})
    # weird timezone bug
    startDate = startDate.replace(hour=0, minute=0)
    endDate = endDate.replace(hour=23, minute=59, second=59)
    log_entries_raw = log.get_entries(user=user, startDate=startDate, endDate=endDate)
    log_entries = [{'entry_id': x.id, 'timestamp': x.timestamp.strftime("%m-%d-%y %I:%M %p"),
                    'clock_type': x.clock_type.id(), 'editing': False}
                        for x in log_entries_raw]
    return jsonify(log_entries)


@timesheet_bp.route('/clock_entries', methods=['GET'])
@login_required
def entries():
    log = NDBTimesheet(Log)
    clock_types = NDBClock_Type(Clock_Type)
    user = current_user
    current_day = {
            'start': datetime.now(pytz.timezone('US/Eastern')).replace(hour=0, minute=0, tzinfo=None),
            'end': datetime.now(pytz.timezone('US/Eastern')).replace(hour=23, minute=59, second=59, tzinfo=None)
        }
    log_entries_raw = log.get_current_entries(user=user.key, timestamp=current_day)
    log_entries = [{ 'timestamp': x.timestamp.strftime("%m-%d-%y %I:%M %p").upper(), 'clock_type': x.clock_type.id()}
                        for x in log_entries_raw]
    return jsonify(log_entries)


@timesheet_bp.route('/clock', methods=['GET', 'POST'])
@login_required
def clock():
    log = NDBTimesheet(Log)
    clock_types = NDBClock_Type(Clock_Type)
    user = current_user
    if user.clocked_in == True:
        button = 'clock-out'
    else:
        button = 'clock-in'
    if request.method == 'POST':
        try:
            data = json.loads(request.data.decode())
        except ValueError:
            return jsonify({'label': button})
        button = data['label']
        clock = clock_types.get_or_create_type(text=button)
        current_timestamp = datetime.now(pytz.timezone('US/Eastern')).replace(tzinfo=None)
        log_entry = log.create_entry(user=user.key, timestamp=current_timestamp, clock_type=clock.key)
        user.clocked_in = not user.clocked_in
        user.put()
        return render_template("timesheet/index.html")
    elif request.method == 'GET': 
        return jsonify({'label': button})
    else:
        return redirect('404.html')

class DateForm(Form):
    startDate = DateField('DatePicker', format='%Y-%m-%d')
    endDate = DateField('DatePicker', format='%Y-%m-%d')
    
@timesheet_bp.route('/history', methods=['GET'])
@login_required
def history():
    form = DateForm()
    user = {}
    user['name'] = current_user.first_name.title() + ' ' + current_user.last_name.title()
    return render_template("timesheet/history.html", form=form, user=user)

@timesheet_bp.route('/history/get_hours', methods=['POST'])
@login_required
def get_hours():
    log = NDBTimesheet(Log)
    user = current_user
    print("testtest2")
    try:
        form = DateForm()
        data = json.loads(request.data.decode())
    except TypeError:
        return jsonify({"worked": None})
    try:
        startDate = parser.parse(data['startDate'])
        endDate = parser.parse(data['endDate'])
    except KeyError:
        return jsonify({"worked": None})
    # weird timezone bug
    startDate = startDate.replace(hour=0, minute=0)
    endDate = endDate.replace(hour=23, minute=59, second=59)
    log_entries = log.get_entries(user=user, startDate=startDate, endDate=endDate)
    print(log_entries)
    difference = [y.timestamp-x.timestamp for x, y in zip(log_entries[0::2], log_entries[1::2])]
    worked = sum(difference, timedelta())
    hours = worked.total_seconds()/3600
    return jsonify({"worked": "{0:.2f}".format(hours)})

