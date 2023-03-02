import json

from instance.config import OPENAI_API_KEY, OPENAI_MAX_USER_REQUESTS_HOUR
from services.helpers import openai_helper

openai_helper.api_key = OPENAI_API_KEY

openai_helper.generate_phishing_email(
    OPENAI_MAX_USER_REQUESTS_HOUR,
    'davide95.v@gmail.com',
    json.load(open('../mocks/proxycurl/example.json'))
)
