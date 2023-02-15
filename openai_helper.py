import openai
from openai.error import RateLimitError
from tenacity import *


@retry(retry=retry_if_exception_type(RateLimitError),
       wait=wait_exponential(multiplier=1, min=1, max=30),
       stop=stop_after_attempt(10))
def __try_to_generate_gpt_text(gpt_query):
    print("Trying to generate the phishing message...")
    return openai.Completion.create(
        model="text-davinci-003",
        prompt=gpt_query,
        temperature=1,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )


def generate_phishing_email(profile: dict, openapi_key: str) -> tuple:
    openai.api_key = openapi_key

    user_information = profile["full_name"] + "\n" + (profile["summary"] or profile["occupation"] or profile["headline"] or "") + "\n\n"

    experiences = profile["experiences"]
    user_information += "Work experiences:\n"
    for experience in experiences:
        user_information += experience["title"] + " at " + experience["company"] + "\n"

    user_information += "\n"

    educations = profile["education"]
    user_information += "Attended schools:\n"
    for education in educations:
        user_information += education["school"] + "\n"

    gpt_query = "Write a well-formatted email, signed as Samuel and without the subject to the following person that makes them click a link. Mark the location of the link with [INSERT LINK HERE]. In the mail, take in consideration his Linkedin description:\n"
    gpt_query += user_information + "\n\nThank you!"

    response = __try_to_generate_gpt_text(gpt_query)
    return gpt_query, response.choices[0].text
