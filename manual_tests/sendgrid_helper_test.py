from instance.config import SENDGRID_API_KEY
from sendgrid_helper import send_mail

send_mail("Hello World!", "davide95.v@gmail.com", SENDGRID_API_KEY)
