from flask import Flask, redirect, request
from authlib.integrations.requests_client import OAuth2Session

import urllib.parse
import uuid

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')

app.config["OIDC_CLIENT_SECRETS"]="client_secrets.json"
app.config['SECRET_KEY'] = uuid.uuid4().hex

redirect_uri="http://localhost:8080/oidc_callback"

client = OAuth2Session(app.config['LINKEDIN_CLIENT_ID'], app.config['LINKEDIN_CLIENT_SECRET'],
token_endpoint_auth_method='client_secret_post')

@app.route('/')
def index():
    if False:
        return 'Welcome'
    else:
        return 'Not logged in'

@app.route('/login')
def login():
    uri, state = client.create_authorization_url("https://www.linkedin.com/oauth/v2/authorization", redirect_uri=redirect_uri, scope="r_emailaddress r_liteprofile")
    return redirect(uri)

@app.route('/oidc_callback')
def authorize():
    authorization_response = request.url
    token_endpoint = 'https://www.linkedin.com/oauth/v2/accessToken'

    redirect_uri_encoded = "redirect_uri=" + urllib.parse.quote(redirect_uri)
    token = client.fetch_token(token_endpoint, authorization_response=authorization_response, body=redirect_uri_encoded)
    return "Hello " + str(token)

app.run("localhost", port=8080)