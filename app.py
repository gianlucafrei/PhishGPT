from flask import Flask, redirect, request, render_template, abort, jsonify
from authlib.integrations.requests_client import OAuth2Session

import urllib.parse
import uuid
import requests
import hmac
import base64
import hashlib
import binascii
import json
import os

import proxycurl_helper

# Setup application
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')

# TODO Overwrite app settings with values from env variables


# Generate a new random secret key for the cookie when starting up
if 'SECRET_KEY' not in app.config:
    app.config['SECRET_KEY'] = uuid.uuid4().hex
bytes_secret_key = binascii.unhexlify(app.config['SECRET_KEY'])

# Setup OIDC client
redirect_uri = app.config['REDIRECT_URI']
client = OAuth2Session(app.config['LINKEDIN_CLIENT_ID'], app.config['LINKEDIN_CLIENT_SECRET'], token_endpoint_auth_method='client_secret_post')

@app.route('/')
def index():
    user_info = get_userinfo_or_false()

    if user_info:
        return render_template('home.html', data=user_info)
    else:
        return render_template('login.html')


# Redirect to this endpoint to start the sign in with LinkedIn process
@app.route('/login')
def login():
    uri, state = client.create_authorization_url("https://www.linkedin.com/oauth/v2/authorization", redirect_uri=redirect_uri, scope="r_emailaddress r_liteprofile")
    return redirect(uri)


@app.route('/send', methods=['POST'])
def sendEmail():

    user_info = get_userinfo_or_false()
    if not user_info:
        abort(401)

    data = request.get_json()
    linked_in_url = data["input-text"]

    # add linked in url if only username is passed
    if not linked_in_url.startswith("https://www.linkedin.com/in/"): linked_in_url = "https://www.linkedin.com/in/" + linked_in_url

    # Load target profile data
    user_data = proxycurl_helper.load_linkedin_data_with_cache(linked_in_url, app.config["NEBULA_API_KEY"])
    return jsonify({'linked_in_url': linked_in_url, 'user_data': user_data})

# This endpoint is called when the user is redirected back from linked in
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
    firstname = profile["localizedFirstName"]
    lastname = profile["localizedLastName"]
    fullname = f"{firstname} {lastname}"

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
    assert verify_token(encoded_token)

    # Safe the token in a cookie and redirect back to main page
    response = redirect("/")
    response.set_cookie('token', encoded_token)
    return response

# Checks the validity of a token
def verify_token(encoded_token):
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
def get_userinfo_or_false():
    encoded_token = request.cookies.get('token')
    if not encoded_token:
        return False

    user_info = verify_token(encoded_token)
    return user_info



if __name__ == '__main__':
    app.run("localhost", port=8080)
