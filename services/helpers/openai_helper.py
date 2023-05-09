import openai
from openai.error import RateLimitError
from tenacity import *
from jinja2 import Template

from dataaccess.DB import DB
from exceptions.openai_max_user_requests_allowed_exception import OpenAiMaxUserRequestsAllowedException

api_key: str


@retry(retry=retry_if_exception_type(RateLimitError),
       wait=wait_exponential(multiplier=1, min=1, max=30),
       stop=stop_after_attempt(10))
def __try_to_generate_gpt_text(openai_request):
    return openai.Completion.create(**openai_request)


def generate_phishing_email(user_max_allowed: int, mail_address: str, profile: dict) -> tuple[dict, str]:
    _stop_if_user_access_not_allowed(user_max_allowed, mail_address)

    openai.api_key = api_key

    with open('templates/prompt.txt', 'r') as file:
        template_str = file.read()

    template = Template(template_str)

    data = {
        'sender': 'Samuel',
        'year': 2023,
        'email_link_reference': 'trace/[DOCUMENT_ID]',
        'recipient': profile['full_name'],
        'about': profile['summary'] or '',
        'occupation': profile['occupation'] or '',
        'headline': profile['headline'] or '',
        'experiences': profile['experiences'],
        'educations': profile['education']
    }

    gpt_query = template.render(**data)

    openai_request = dict(
        model='text-davinci-003',
        prompt=gpt_query,
        temperature=1,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    response = __try_to_generate_gpt_text(openai_request)
    return openai_request, response.choices[0].text.strip()


def extract_subject_mail(text: str) -> tuple[str, str]:
    subject = text.split('\n')[0].split('Subject:')[1].strip()
    mail = '\n'.join(text.split('\n')[1:]).strip()
    return subject, mail


def _stop_if_user_access_not_allowed(user_max_allowed: int, mail_address: str):
    if user_max_allowed <= DB.get_instance().get_number_of_openai_api_requests_last_hour(mail_address):
        raise OpenAiMaxUserRequestsAllowedException
