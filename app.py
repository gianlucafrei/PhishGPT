from flask import Flask, redirect, request, render_template, abort, jsonify, send_file, url_for, make_response
from authlib.integrations.requests_client import OAuth2Session
from io import BytesIO


import os
import csv
import io
import datetime
import imghdr

from dataaccess import db
from services import auth_service, phish_service
from services.helpers import proxycurl_helper, openai_helper, sendgrid_helper

app = Flask(__name__, instance_relative_config=True)
client: OAuth2Session


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


@app.route('/profile_image/<username>')
def get_profile_image(username):
    image = phish_service.get_profile_image_by_username(username)
    if image:
        image_data = BytesIO(image)
        mimetype = '' if imghdr.what(image_data) else 'image/svg+xml'
        return send_file(image_data, mimetype=mimetype)
    else:
        return 'User has not been loaded yet. Cannot fetch the profile image', 404


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
    response = phish_service.phish(user_info, linkedin_url)

    if response['success']:
        url_profile_image = url_for(
            'get_profile_image',
            username=phish_service.get_username_from_url(linkedin_url),
            _external=True
        )
        response['profile_image'] = url_profile_image

    return jsonify(response)


@app.route('/oidc_callback')
def oidc_callback():
    encoded_token = auth_service.authorize(client, request.url, app.config['REDIRECT_URI'])
    response = redirect('/')
    response.set_cookie('token', encoded_token.decode())
    return response


@app.route('/export-all-mail', methods=['GET'])
def export_all_email():
    user_info = auth_service.verify_token(__get_token_cookie())
    authorized_users = app.config['AUTHORIZED_USERS'].split(':')
    if not user_info or user_info.get('email') not in authorized_users:
        abort(401)

    # Load the request and responses stored in the database
    data = db.get_all_generated_mail()
 
    # Get the date time string for the filename
    dt = datetime.datetime.now()
    str_date = dt.strftime('%Y%m%d_%H%M%S')
    filename = 'data_' + str_date + '.csv'

    fieldnames = ['openai_request.prompt', 'mail']

    return __generate_csv(fieldnames, filename, data)


@app.route('/readiness')
def readiness():
    is_mongo_up = db.is_up()
    openai_usage = openai_helper.get_usage()
    proxycurl_credit = proxycurl_helper.get_credits()

    state = {
        'mongo_connection': {'value': is_mongo_up},
        'openai_usage': {'value': openai_usage},
        'proxycurl_credit': {'value': proxycurl_credit}
    }

    if not is_mongo_up:
        state['mongo_connection']['error'] = 'Service is down'

    if openai_usage >= float(app.config['OPENAI_THRESHOLD']):
        state['openai_usage']['error'] = 'Payment required'

    if proxycurl_credit <= int(app.config['PROXYCURL_THRESHOLD']):
        state['proxycurl_credit']['error'] = 'Payment required'

    success = all(['error' not in state[key] for key in state.keys()])
    if not success:
        abort(make_response(jsonify(message=state), 500))

    return state


def __generate_csv(fieldnames, filename, data):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for item in data:
        writer.writerow(item)
    response = make_response(output.getvalue().encode('utf-8'))
    response.headers['Content-Disposition'] = 'attachment; filename='+filename
    response.headers['Content-Type'] = 'text/csv'
    return response


def __get_token_cookie() -> bytes:
    return str.encode(request.cookies.get('token'))


def __load_config():
    for env in os.environ:
        app.config[env] = os.environ[env]
    if os.path.exists('instance/config.py'):
        app.config.from_pyfile('config.py')


if __name__ == '__main__':
    __load_config()

    client = OAuth2Session(
        app.config['LINKEDIN_CLIENT_ID'],
        app.config['LINKEDIN_CLIENT_SECRET'],
        token_endpoint_auth_method='client_secret_post'
    )

    proxycurl_helper.api_key = app.config['NEBULA_API_KEY']
    openai_helper.api_key = app.config['OPENAI_API_KEY']
    sendgrid_helper.api_key = app.config['SENDGRID_API_KEY']
    db.connect(app.config['MONGO_CONNECTION'], app.config['MONGO_DB'], app.config['MONGO_USER'], app.config['MONGO_PASSWORD'])

    app.static_url_path = '/static'
    app.run('localhost', port=8080)
