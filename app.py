from flask import Flask, redirect, request, render_template, abort, jsonify, send_file, url_for, make_response
from authlib.integrations.requests_client import OAuth2Session
from io import BytesIO


import os
import imghdr

from dataaccess.DB import DB
from dataaccess.inmemory_db import InMemoryDB
from dataaccess.mongo_db import MongoDB
from services import auth_service, phish_service, readiness_service, export_service
from services.helpers import proxycurl_helper, openai_helper, sendgrid_helper

app = Flask(__name__, instance_relative_config=True)

for env in os.environ:
    app.config[env] = os.environ[env]
if os.path.exists('instance/config.py'):
    app.config.from_pyfile('config.py')

client = OAuth2Session(
    app.config['LINKEDIN_CLIENT_ID'],
    app.config['LINKEDIN_CLIENT_SECRET'],
    token_endpoint_auth_method='client_secret_post'
)

proxycurl_helper.api_key = app.config['NEBULA_API_KEY']
openai_helper.api_key = app.config['OPENAI_API_KEY']
sendgrid_helper.api_key = app.config['SENDGRID_API_KEY']

persistence_strategy = app.config['PERSISTENCE_STRATEGY']
if persistence_strategy == 'mongo':
    DB.get_instance().set_db_type(MongoDB(
        app.config['MONGO_CONNECTION'],
        app.config['MONGO_DB'],
        app.config['MONGO_USER'],
        app.config['MONGO_PASSWORD'])
    )
elif persistence_strategy == 'in-memory':
    DB.get_instance().set_db_type(InMemoryDB())
else:
    raise Exception("Invalid persistence name")


@app.route('/')
def index():
    user_info = auth_service.verify_token(__get_token_cookie())
    if user_info:
        return render_template('home.html', data=user_info)
    else:
        return render_template('login.html')


@app.route('/login')
def login():
    uri, state = client.create_authorization_url(
        'https://www.linkedin.com/oauth/v2/authorization',
        redirect_uri=app.config['REDIRECT_URI'],
        scope='r_emailaddress r_liteprofile'
    )
    return redirect(uri)


@app.route('/oidc_callback')
def oidc_callback():
    encoded_token = auth_service.authorize(client, request.url, app.config['REDIRECT_URI'])
    response = redirect('/')
    response.set_cookie('token', encoded_token.decode())
    return response


@app.route('/send', methods=['POST'])
def send():
    user_info = auth_service.verify_token(__get_token_cookie())
    if not user_info:
        abort(401)

    user_input = request.get_json()['input-text']
    if not user_input:
        return {
            'success': False,
            'user_response': 'Empty input'
        }

    linkedin_url = phish_service.adjust_for_linkedin_url(user_input)
    response = phish_service.phish(
        user_info,
        linkedin_url,
        int(app.config['PROXYCURL_MAX_USER_REQUESTS_HOUR']),
        int(app.config['OPENAI_MAX_USER_REQUESTS_HOUR'])
    )

    if response['success']:
        url_profile_image = url_for(
            'get_profile_image',
            username=phish_service.get_username_from_url(linkedin_url),
            _external=True
        )
        response['profile_image'] = url_profile_image

    return jsonify(response)


@app.route('/profile_image/<username>')
def get_profile_image(username):
    image = phish_service.get_profile_image_by_username(username)
    if image:
        image_data = BytesIO(image)
        mimetype = '' if imghdr.what(image_data) else 'image/svg+xml'
        return send_file(image_data, mimetype=mimetype)
    else:
        return 'User has not been loaded yet. Cannot fetch the profile image', 404


@app.route('/trace/<email_id>')
def trace_email_link_click(email_id: str):
    return render_template('scam.html', data=email_id)


@app.route('/export-all-mail', methods=['GET'])
def export_all_email():
    user_info = auth_service.verify_token(__get_token_cookie())
    authorized_users = app.config['AUTHORIZED_USERS'].split(':')
    if not user_info or user_info.get('email') not in authorized_users:
        abort(401)

    filename, content = export_service.export_all_mails()

    response = make_response(content)
    response.headers['Content-Disposition'] = 'attachment; filename=' + filename
    response.headers['Content-Type'] = 'text/csv'

    return response


@app.route('/readiness')
def readiness():
    state = readiness_service.check(app.config['OPENAI_THRESHOLD'], app.config['PROXYCURL_THRESHOLD'])
    success = all(['error' not in state[key] for key in state.keys()])
    if not success:
        abort(make_response(jsonify(message=state), 500))
    return state


def __get_token_cookie() -> bytes or None:
    token = request.cookies.get('token')
    return str.encode(token) if token is not None else None


if __name__ == '__main__':
    app.static_url_path = '/static'
    app.run('localhost', port=8080)
