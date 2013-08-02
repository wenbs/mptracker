import flask
from flask.ext.login import LoginManager
from flask.ext.browserid import BrowserID
from mptracker import models

login_manager = LoginManager()

browser_id = BrowserID()

auth = flask.Blueprint('auth', __name__)


@login_manager.user_loader
def get_user_by_id(user_id):
    return models.User.query.get(user_id)


@browser_id.user_loader
def get_user(user_data):
    assert user_data['status'] == 'okay'
    return models.User.get_or_create(email=user_data['email'])


@auth.record
def register_login(state):
    login_manager.init_app(state.app)
    browser_id.init_app(state.app)


@auth.route('/login')
def login():
    return flask.render_template('login.html')