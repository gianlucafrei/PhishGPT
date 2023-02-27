import base64
import binascii
import json
import hashlib
import hmac
import requests
import uuid
import urllib.parse

from authlib.oauth2 import OAuth2Client


BYTES_SECRET_KEY = binascii.unhexlify(uuid.uuid4().hex)


def authorize(client: OAuth2Client, authorization_response: str, redirect_url: str) -> bytes:
    access_token = __exchange_access_code(client, authorization_response, redirect_url)

    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f"Bearer {access_token}"}

    profile = __get_profile(headers)
    email = __get_mail(headers)

    encoded_token = __create_authenticated_cookie(profile, email)

    if not verify_token(encoded_token):
        raise Exception('Invalid token')
    return encoded_token


def verify_token(encoded_token: bytes) -> dict or bool:
    if not encoded_token:
        return False
    try:
        decoded_token = base64.urlsafe_b64decode(encoded_token)
        decoded_user_info = decoded_token[:-32]
        decoded_signature = decoded_token[-32:]
        computed_signature = hmac.new(BYTES_SECRET_KEY, decoded_user_info, hashlib.sha256).digest()

        token_valid = hmac.compare_digest(computed_signature, decoded_signature)

        if token_valid:
            user_info_str = decoded_user_info.decode('utf-8')
            user_info = json.loads(user_info_str)
            return user_info
        else:
            return False
    except (Exception,):
        return False


def __exchange_access_code(client: OAuth2Client, authorization_response: str, redirect_url: str) -> str:
    token_endpoint = 'https://www.linkedin.com/oauth/v2/accessToken'
    redirect_uri_encoded = f"redirect_uri={urllib.parse.quote(redirect_url)}"
    token = client.fetch_token(token_endpoint, authorization_response=authorization_response, body=redirect_uri_encoded)
    return token['access_token']


def __get_profile(headers: dict) -> dict:
    profile_api_url = 'https://api.linkedin.com/v2/me'
    response = requests.get(url=profile_api_url, headers=headers)
    return response.json()


def __get_mail(headers: dict) -> str:
    email_api_url = 'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))'
    email_response = requests.get(url=email_api_url, headers=headers)
    email_response_body = email_response.json()
    return email_response_body['elements'][0]['handle~']['emailAddress']


def __create_authenticated_cookie(profile: dict, mail: str):
    user_info = {'profile': profile, 'email': mail}
    user_info_bytes = json.dumps(user_info).encode('utf-8')
    signature = hmac.new(BYTES_SECRET_KEY, user_info_bytes, hashlib.sha256).digest()
    token = user_info_bytes + signature
    return base64.urlsafe_b64encode(token)
