from instance.config import SENDGRID_API_KEY
from services.helpers import sendgrid_helper

sendgrid_helper.api_key = SENDGRID_API_KEY
sendgrid_helper.send_mail('Hello World!', 'davide95.v@gmail.com')
