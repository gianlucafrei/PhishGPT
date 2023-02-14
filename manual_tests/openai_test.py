import json

from instance.config import OPENAI_API_KEY
from openai_helper import generate_phishing_email

generate_phishing_email(json.load(open("../draft/proxycurl.json")), OPENAI_API_KEY)
