import json

from instance.config import OPENAI_API_KEY
from services.helpers import openai_helper

openai_helper.api_key = OPENAI_API_KEY
openai_helper.generate_phishing_email(json.load(open('../mocks/proxycurl/example.json')))
