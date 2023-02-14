import sendgrid
from sendgrid.helpers.mail import *


def send_mail(text: str, address: str, sendgrid_api_key: str):
    sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
    from_email = Email("davide.vanoni@zuehlke.com")
    to_email = To(address)
    subject = "Sending with SendGrid is Fun"
    content = Content("text/plain", text)
    mail = Mail(from_email, to_email, subject, content)
    sg.client.mail.send.post(request_body=mail.get())
