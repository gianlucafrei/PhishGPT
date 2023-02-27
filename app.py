from flask import Flask, redirect, request, render_template, abort, jsonify, send_file, url_for, make_response
from authlib.integrations.requests_client import OAuth2Session
from io import BytesIO
from expiringdict import ExpiringDict

import urllib.parse
import uuid
import requests
import hmac
import base64
import hashlib
import binascii
import json
import os
import csv
import io
import datetime
import imghdr

import openai_helper
import proxycurl_helper
from db import DB
from exceptions.nubela_auth_exception import NubelaAuthException
from exceptions.nubela_profile_not_found_exception import NubelaProfileNotFoundException
from exceptions.nubela_profile_not_enough_information_exception import NubelaProfileNotEnoughInformationException

# Setup application
app = Flask(__name__, instance_relative_config=True)

# Load from system environment
for env in os.environ:
    app.config[env] = os.environ[env]

if os.path.exists("instance/../config.py"):
    # Load from application environment
    app.config.from_pyfile('../config.py')

if os.path.exists("instance/config.py"):
    # Load from private application environment
    app.config.from_pyfile('config.py')


# Generate a new random secret key for the cookie when starting up
if 'SECRET_KEY' not in app.config or app.config['SECRET_KEY'] is None:
    app.config['SECRET_KEY'] = uuid.uuid4().hex
bytes_secret_key = binascii.unhexlify(app.config['SECRET_KEY'])

# Setup OIDC client
redirect_uri = app.config['REDIRECT_URI']
client = OAuth2Session(app.config['LINKEDIN_CLIENT_ID'], app.config['LINKEDIN_CLIENT_SECRET'], token_endpoint_auth_method='client_secret_post')

profile_images_cache = ExpiringDict(max_len=1000, max_age_seconds=300)


@app.route('/')
def index():
    user_info = __get_userinfo_or_false()

    if user_info:
        return render_template('home.html', data=user_info)
    else:
        return render_template('login.html')


# Redirect to this endpoint to start the sign in with LinkedIn process
@app.route('/login')
def login():
    uri, state = client.create_authorization_url("https://www.linkedin.com/oauth/v2/authorization", redirect_uri=redirect_uri, scope="r_emailaddress r_liteprofile")
    return redirect(uri)


@app.route('/profile_image/<username>')
def get_profile_image(username):
    image = profile_images_cache.get(username)
    if image:
        image_data = BytesIO(image)
        mimetype = "" if imghdr.what(image_data) else "image/svg+xml"
        return send_file(image_data, mimetype=mimetype)
    else:
        return 'User has not been loaded yet. Cannot fetch the profile image', 404


@app.route('/send', methods=['POST'])
def send_email():
    user_info = __get_userinfo_or_false()
    if not user_info:
        abort(401)

    data = request.get_json()
    linked_in_input = data["input-text"]

    if not linked_in_input:
        return jsonify({
            'success': False,
            'user_response': "Empty input"
        })

    if not linked_in_input.startswith("https://www.linkedin.com/in/"):
        linked_in_url = "https://www.linkedin.com/in/" + linked_in_input
    elif linked_in_input.endswith("/"):
        linked_in_url = linked_in_input[:-1]
    else:
        linked_in_url = linked_in_input

    username = linked_in_url[linked_in_url.rfind("/") + 1:]

    db = DB(app.config['MONGO_CONNECTION'], app.config['MONGO_DB'], app.config['MONGO_USER'], app.config['MONGO_PASSWORD'])

    from_api = False
    profile_image = None
    if username == 'example':
        with open("mocks/proxycurl/example.json", "r") as file:
            user_data = json.loads(file.read())
    else:
        profile_image, user_data = db.get_linked_in_data_by_username(username)

    try:
        if not user_data:
            from_api = True
            user_data = proxycurl_helper.load_linkedin_data(linked_in_url, app.config["NEBULA_API_KEY"])
            profile_image = requests.get(user_data['profile_pic_url']).content

        proxycurl_helper.check_enough_information_in_profile(user_data)
             
        gpt_request, gpt_response = openai_helper.generate_phishing_email(user_data, app.config["OPENAI_API_KEY"])

        profile_images_cache[username] = profile_image

        db.add_phish(user_info, from_api, user_data, profile_image, gpt_request, gpt_response)

        url_profile_image = url_for('get_profile_image', username=username, _external=True)

        return jsonify({
            'success': True,
            'user_response': gpt_response.strip(),
            'profile_image': url_profile_image
        })
    except (NubelaAuthException, NubelaProfileNotFoundException, NubelaProfileNotEnoughInformationException) as e:
        db.add_error(user_info, linked_in_input, type(e).__name__, e.message)
        return jsonify({
            'success': False,
            'user_response': e.message
        })


@app.route('/oidc_callback')
def authorize():
    # Exchange access code for authorization token
    authorization_response = request.url
    token_endpoint = 'https://www.linkedin.com/oauth/v2/accessToken'
    redirect_uri_encoded = "redirect_uri=" + urllib.parse.quote(redirect_uri)
    token = client.fetch_token(token_endpoint, authorization_response=authorization_response, body=redirect_uri_encoded)
    access_token = token['access_token']

    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer {}'.format(access_token)}

    # Load user profile
    profile_api_url = "https://api.linkedin.com/v2/me"
    response = requests.get(url=profile_api_url, headers=headers)
    profile = response.json()

    # Load user email address
    email_api_url = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"
    email_response = requests.get(url=email_api_url, headers=headers)
    email_response_body = email_response.json()
    email = email_response_body["elements"][0]["handle~"]["emailAddress"]

    # Create an authenticated cookie that stores the information
    user_info = {"profile": profile, "email": email}
    user_info_bytes = json.dumps(user_info).encode('utf-8')
    signature = hmac.new(bytes_secret_key, user_info_bytes, hashlib.sha256).digest()
    token = user_info_bytes + signature
    encoded_token = base64.urlsafe_b64encode(token)
    assert __verify_token(encoded_token)

    # Safe the token in a cookie and redirect back to main page
    response = redirect("/")
    response.set_cookie('token', encoded_token)
    return response


@app.route('/export-all-mail', methods=['GET'])
def export_all_email():
    # Check whether user is authenticated and authorized to call the endpoint
    user_info = __get_userinfo_or_false()
    authorized_users = app.config['AUTHORIZED_USERS'].split(':')
    if not user_info or user_info.get('email') not in authorized_users:
        abort(401)

    # Load the request and responses stored in the database
    db = DB(app.config['MONGO_CONNECTION'], app.config['MONGO_DB'], app.config['MONGO_USER'], app.config['MONGO_PASSWORD'])
    data = db.get_all_generated_mail()
 
    # Get the date time string for the filename
    dt = datetime.datetime.now()
    str_date = dt.strftime("%Y%m%d_%H%M%S")
    filename = 'data_' + str_date +".csv"

    fieldnames = ['openai_request.prompt', 'mail']

    # TODO: ERROR HANDLING

    return __generate_csv(fieldnames, filename, data)


# Function to generate a CSV file from a dictionary
def __generate_csv(fieldnames, filename, data):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for item in data:
        writer.writerow(item)
    response = make_response(output.getvalue().encode('utf-8'))
    response.headers['Content-Disposition'] = 'attachment; filename='+filename
    response.headers['Content-Type'] = 'text/csv'

    # TODO: ERROR HANDLING

    return response


@app.route('/readiness')
def readiness():
    db = DB(app.config['MONGO_CONNECTION'], app.config['MONGO_DB'], app.config['MONGO_USER'], app.config['MONGO_PASSWORD'])

    is_mongo_up = db.is_up()
    openai_usage = openai_helper.get_usage(app.config["OPENAI_API_KEY"])
    proxycurl_credit = proxycurl_helper.get_credits(app.config["NEBULA_API_KEY"])

    state = {
        'mongo_connection': {'value': is_mongo_up},
        'openai_usage': {'value': openai_usage},
        'proxycurl_credit': {'value': proxycurl_credit}
    }

    if not is_mongo_up:
        state['mongo_connection']['error'] = 'Service is down'

    if openai_usage >= float(app.config["OPENAI_THRESHOLD"]):
        state['openai_usage']['error'] = 'Payment required'

    if proxycurl_credit <= int(app.config["PROXYCURL_THRESHOLD"]):
        state['proxycurl_credit']['error'] = 'Payment required'

    success = all(['error' not in state[key] for key in state.keys()])
    if not success:
        abort(make_response(jsonify(message=state), 500))

    return state


# Checks the validity of a token
def __verify_token(encoded_token):
    try:
        decoded_token = base64.urlsafe_b64decode(encoded_token)
        decoded_user_info = decoded_token[:-32]
        decoded_signature = decoded_token[-32:]
        computed_signature = hmac.new(bytes_secret_key, decoded_user_info, hashlib.sha256).digest()

        token_valid = hmac.compare_digest(computed_signature, decoded_signature)

        if token_valid:
            user_info_str = decoded_user_info.decode('utf-8')
            user_info = json.loads(user_info_str)
            return user_info
        else:
            return False
    except:
        return False


# Get the token from the request (if present) and validates it
def __get_userinfo_or_false():
    encoded_token = request.cookies.get('token')
    if not encoded_token:
        return False

    user_info = __verify_token(encoded_token)
    return user_info


if __name__ == '__main__':
    app.static_url_path = "/static"
    app.run("localhost", port=8080)
