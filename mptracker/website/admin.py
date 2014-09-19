import flask
from flask.ext.oauthlib.client import OAuth

admin = flask.Blueprint('admin', __name__)


def setup_admin(app):
    oauth = OAuth(app)
    google = oauth.remote_app(
        'google',
        consumer_key=app.config['GLOGIN_CLIENT_ID'],
        consumer_secret=app.config['GLOGIN_CLIENT_SECRET'],
        request_token_params={
            'scope': 'https://www.googleapis.com/auth/userinfo.email'},
        base_url='https://www.googleapis.com/oauth2/v1/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
    )

    @app.route('/admin/login')
    def login():
        url = flask.url_for('authorized', _external=True)
        return google.authorize(callback=url)

    @app.route('/admin/logout')
    def logout():
        flask.session.pop('identity', None)
        return flask.redirect(flask.url_for('admin.home'))

    @app.route('/admin/login/google')
    @google.authorized_handler
    def authorized(resp):
        if resp is None:
            return 'Access denied: reason=%s error=%s' % (
                flask.request.args['error_reason'],
                flask.request.args['error_description'],
            )
        flask.session['identity'] = {
            'google_token': (resp['access_token'], ''),
        }
        me = google.get('userinfo')
        flask.session['identity']['name'] = me.data['name']
        flask.session['identity']['email'] = me.data['email']
        flask.session['identity']['picture'] = me.data['picture']
        return flask.redirect(flask.url_for('admin.home'))

    @google.tokengetter
    def get_google_oauth_token():
        return flask.session.get('identity', {}).get('google_token')

    app.register_blueprint(admin)


@admin.route('/admin')
def home():
    return repr(flask.session.get('identity'))
