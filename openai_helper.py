import json

import openai
import requests
from openai.error import RateLimitError
from tenacity import *


@retry(retry=retry_if_exception_type(RateLimitError),
       wait=wait_exponential(multiplier=1, min=1, max=30),
       stop=stop_after_attempt(10))
def __try_to_generate_gpt_text(openai_request):
    print("Trying to generate the phishing message...")
    return openai.Completion.create(**openai_request)


def generate_phishing_email(profile: dict, openapi_key: str) -> tuple[dict, str]:
    openai.api_key = openapi_key

    user_information = profile["full_name"] + "\n"

    user_information += (profile["summary"] or "") + "\n"
    user_information += (profile["occupation"] or "") + "\n"
    user_information += (profile["headline"] or "") + "\n"

    user_information += "\n"
    experiences = profile["experiences"]
    if experiences:
        user_information += "Work experiences:\n"
        for experience in experiences:
            user_information += experience["title"] + " at " + experience["company"] + "\n"

    user_information += "\n"
    educations = profile["education"]
    if educations:
        user_information += "Attended schools:\n"
        for education in educations:
            user_information += education["school"] + "\n"

    gpt_query = "Write a well-formatted email, signed as Samuel and without the subject to the following person that makes them click a link. Mark the location of the link with [INSERT LINK HERE]. In the mail, take in consideration his Linkedin description:\n"
    gpt_query += user_information + "\n\nThank you!"

    openai_request = dict(
        model="text-davinci-003",
        prompt=gpt_query,
        temperature=1,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    response = __try_to_generate_gpt_text(openai_request)
    return openai_request, response.choices[0].text


def get_usage(openapi_key: str) -> float or bool:
    # other undocumented endpoint: https://api.openai.com/dashboard/billing/usage
    api_endpoint = 'https://api.openai.com/dashboard/billing/credit_grants'
    header_dic = {'Authorization': 'Bearer ' + openapi_key}
    response = requests.get(api_endpoint, headers=header_dic)
    if response.status_code == 200:
        return json.loads(response.content)['total_used']
    return False
