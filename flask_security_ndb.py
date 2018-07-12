# -*- coding: utf-8 -*-
"""
.. module:: flask_security_ndb
   :synopsis: Google App Engine NDB support for Flask-Security

The :mod:`<flask_security_ndb>` module adds support for the Google App Engine datastore using NDB

"""
from flask_security import datastore, UserMixin, RoleMixin
from google.appengine.ext import ndb
from google.appengine.api import mail
import datetime

__all__ = ['Role', 'User', 'NDBUserDatastore']

class NDBBase(ndb.Model):
    @property
    def id(self):
        """Override for getting the ID.

        Resolves NotImplementedError: No `id` attribute - override `get_id`

        :rtype: str
        """
        return self.key.id()

class Role(NDBBase, RoleMixin):
    name = ndb.StringProperty()
    description = ndb.StringProperty()


class User(NDBBase, UserMixin):
    first_name = ndb.StringProperty(required=True)
    last_name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)
    active = ndb.BooleanProperty(default=True)
    confirmed_at = ndb.DateTimeProperty(default=datetime.datetime.now())
    last_login_at = ndb.DateTimeProperty()
    current_login_at = ndb.DateTimeProperty()
    last_login_ip = ndb.TextProperty(indexed=True)
    current_login_ip = ndb.TextProperty()
    roles_ = ndb.KeyProperty(Role, repeated=True)
    clocked_in = ndb.BooleanProperty(default=False)
    login_count = ndb.IntegerProperty()

    def __init__(self, *args, **kwargs):
        self._roles_cache = []
        roles = [r.key for r in kwargs.pop('roles', [])]
        super(User, self).__init__(*args, **kwargs)
        self.roles_ = roles

    @property
    def roles(self):
        if len(self._roles_cache) != len(self.roles_):
            self._roles_cache = ndb.get_multi(self.roles_)
        return self._roles_cache

    @roles.setter
    def roles(self, role):
        self._roles_cache.append(role)
        self.roles_.append(role.key)

class Clock_Type(NDBBase):
    text = ndb.TextProperty()

class Log(NDBBase):
    user = ndb.KeyProperty(User)
    timestamp = ndb.DateTimeProperty()
    clock_type = ndb.KeyProperty(Clock_Type)
    
class NDBDatastore(datastore.Datastore):
    """Datastore adapter for NDB"""

    def __init__(self, *args, **kwargs):
        """No need to set self.db"""
        pass

    def put(self, model):
        """Saves a model to the datastore

        :param ndb.Model model: The model to save
        :return: The new entity
        :rtype: ndb.Model
        """
        model.put()
        return model

    def delete(self, model):
        """Deletes a model

        :param ndb.Model model: The ndb entity to delete
        """
        model.key.delete(use_datastore=False)
        model.key.delete()

class NDBClock_Type(NDBDatastore):
    def __init__(self, clock_type_model):
        self.clock_type_model = clock_type_model

    def get_type(self, text):
        return self.clock_type_model.get_by_id(text)

    def get_all(self):
        return self.clock_type_model.query().fetch()

    def create_type(self, **kwargs):
        kwargs['id'] = kwargs.get('text', None)
        type = self.clock_type_model(**kwargs)
        return self.put(type)

    def find_type(self, **kwargs):
        if 'id' in kwargs:
            return self.get_type(kwargs['id'])
        filters = [getattr(self.clock_type_model, k) == v
                   for k, v in kwargs.iteritems() if hasattr(self.clock_type_model, k)]
        return self.clock_type_model.query(*filters).get()

    def get_or_create_type(self, text, **kwargs):
        kwargs["text"] = text
        return self.get_type(text) or self.create_type(**kwargs)

    def delete_type(self, clock_type):
        self.delete(clock_type)

class NDBTimesheet(NDBDatastore):
    def __init__(self, log_model):
        self.log_model = log_model
    
    def create_entry(self, **kwargs):
        #kwargs['id'] = kwargs.get('email', None)
        log_entry = self.log_model(**kwargs)
        return self.put(log_entry)

    def get_entry(self, log_id):
        return self.log_model.get_by_id(log_id)

    def delete_entry_by_id(self, log_id):
        log = self.get_entry(log_id)
        self.delete(log)
    """ Returns the most recent timeclock entry

    :param ndb.Model.key user.key: a user's key object
    """
    def get_entries(self, **kwargs):
        user = kwargs.get('user')
        filters = [ndb.AND(getattr(self.log_model, 'user') == user.key)]
        startDate = kwargs.get('startDate').replace(tzinfo=None);
        endDate = kwargs.get('endDate').replace(tzinfo=None);
        if startDate == endDate:
            endDate = datetime.datetime(startDate.year, startDate.month, startDate.day, 23, 59, 59)
        filters.append(ndb.AND(getattr(self.log_model, 'timestamp') >= startDate, getattr(self.log_model, 'timestamp') <= endDate))
        return self.log_model.query(*filters).order(getattr(self.log_model, 'timestamp')).fetch()

    def get_current_entries(self, user, timestamp):
        import datetime
        filters = [ndb.AND(getattr(self.log_model, 'user') == user)]
        start = timestamp['start']
        end = timestamp['end']
        filters.append(ndb.AND(getattr(self.log_model, 'timestamp') >= start, getattr(self.log_model, 'timestamp') <= end))
        return self.log_model.query(*filters).order(-getattr(self.log_model, 'timestamp')).fetch()


class NDBUserDatastore(NDBDatastore, datastore.UserDatastore):
    """An NDB datastore implementation for Flask-Security."""

    def __init__(self, user_model, role_model):
        """Initializes the User Datastore.

        :param ndb.Model user_model: A user model class definition
        :param ndb.Model role_model: A role model class definition
        """
        NDBDatastore.__init__(self)
        datastore.UserDatastore.__init__(self, user_model, role_model)

    def _prepare_role_modify_args(self, user, role):
        string_types = basestring;
        if isinstance(user, string_types):
            user = self.find_user(email=user)
        if isinstance(role, string_types):
            role = self.find_role(role)
        return user, role

    def create_user(self, **kwargs):
        """App Engine override to set email as the :class:`ndb.Key`'s id"""
        kwargs['id'] = kwargs.get('email', None)
        return super(NDBUserDatastore, self).create_user(**kwargs)

    def create_role(self, **kwargs):
        """App Engine override to set name as the :class:`ndb.Key`'s id"""
        kwargs['id'] = kwargs.get('name', None)
        return super(NDBUserDatastore, self).create_role(**kwargs)

    def get_user(self, id_or_email):
        """Returns a user matching the specified ID or email address.

        :param str id_or_email: User's ID (email address)
        :rtype: User or None
        """
        return self.user_model.get_by_id(id_or_email)

    def get_users(self):
        """
        projection = [getattr(self.user_model, 'id'),
                        getattr(self.user_model, 'first_name'),
                        getattr(self.user_model, 'last_name'),
                        getattr(self.user_model, 'last_login_ip'),
                        getattr(self.user_model, 'current_login_ip'),
                        getattr(self.user_model, 'roles')
                    ]
                    """
        projection = ['email','first_name','last_name', 'last_login_ip', 'clocked_in']
        return self.user_model.query(projection=projection).fetch()

    def find_user(self, **kwargs):
        """Returns a user matching the provided parameters.

        :rtype: User or None
        """
        if 'id' in kwargs:
            return self.get_user(kwargs['id'])
        filters = [getattr(self.user_model, k) == v
                   for k, v in kwargs.iteritems() if hasattr(self.user_model, k)]
        return self.user_model.query(*filters).get()
    
    def find_role(self, role):
        """Returns a role matching the provided name.

        :param str role: Role name
        :rtype: Role or None
        """
        return self.role_model.get_by_id(role)
    
    def add_role_to_user(self, user, role):
        user, role = self._prepare_role_modify_args(user, role)
        if role not in user.roles:
            user.roles = role
            self.put(user)
            return True
        return False

def send_email(message):
    """Sends a :class:`flask_mail.Message` using the GAE infrastructure

    :param flask_mail.Message message:
    """
    mail.send_mail(message.sender, message.send_to, message.subject,
                   body=message.body, html=message.html)
