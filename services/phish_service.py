import datetime
import json
import requests

from expiringdict import ExpiringDict

from dataaccess.DB import DB
from exceptions.nubela_auth_exception import NubelaAuthException
from exceptions.nubela_max_user_requests_allowed_exception import NubelaMaxUserRequestsAllowedException
from exceptions.nubela_profile_not_enough_information_exception import NubelaProfileNotEnoughInformationException
from exceptions.nubela_profile_not_found_exception import NubelaProfileNotFoundException
from exceptions.openai_max_user_requests_allowed_exception import OpenAiMaxUserRequestsAllowedException
from services.helpers import proxycurl_helper, openai_helper


PROFILE_IMAGES_CACHE = ExpiringDict(max_len=1000, max_age_seconds=300)


def phish(user_info: dict, linkedin_url: str, user_max_allowed_nubela: int, user_max_allowed_openai: int) -> dict:
    linkedin_username = get_username_from_url(linkedin_url)

    from_api = False
    profile_image = None
    if linkedin_username == 'example':
        with open('mocks/proxycurl/example.json', 'r') as file:
            user_data = json.loads(file.read())
    else:
        profile_image, user_data = DB.get_instance().get_linked_in_data_by_username(linkedin_username)

    try:
        if not user_data:
            from_api = True
            user_data = proxycurl_helper.load_linkedin_data(user_max_allowed_nubela, user_info['email'], linkedin_url)
            profile_image = requests.get(user_data['profile_pic_url']).content

        proxycurl_helper.check_enough_information_in_profile(user_data)

        gpt_request, gpt_response = openai_helper.generate_phishing_email(user_max_allowed_openai, user_info['email'], user_data)

        PROFILE_IMAGES_CACHE[linkedin_username] = profile_image

        subject, mail = openai_helper.extract_subject_mail(gpt_response)

        id_phish = DB.get_instance().add_phish(user_info, from_api, user_data, profile_image, gpt_request, subject, mail)

        gpt_response = gpt_response.replace("[DOCUMENT_ID]", id_phish)

        return {
            'success': True,
            'user_response': gpt_response,
            'profile_image': None
        }
    except (NubelaAuthException, NubelaProfileNotFoundException, NubelaProfileNotEnoughInformationException,
            NubelaMaxUserRequestsAllowedException, OpenAiMaxUserRequestsAllowedException) as e:
        DB.get_instance().add_error(user_info, linkedin_url, type(e).__name__, e.message)
        return {
            'success': False,
            'user_response': e.message
        }


def get_profile_image_by_username(username: str) -> bytes:
    return PROFILE_IMAGES_CACHE.get(username)


def get_username_from_url(linkedin_url: str) -> str:
    return linkedin_url[linkedin_url.rfind('/') + 1:]


def adjust_for_linkedin_url(user_input: str) -> str:
    if not user_input.startswith('https://www.linkedin.com/in/'):
        return 'https://www.linkedin.com/in/' + user_input
    elif user_input.endswith('/'):
        return user_input[:-1]
    return user_input

def get_all_phishing_email_requested_by_user(user_info: dict) -> list[dict]:
    phishing_emails = DB.get_instance().get_previous_phishing_email_generated_by_user(user_info['email'])

    for item in phishing_emails:
        public_identifier = item.get('linkedin_data.public_identifier','')

        if public_identifier not in PROFILE_IMAGES_CACHE:
            profile_image = item.get('profile_image','')
            PROFILE_IMAGES_CACHE[public_identifier] = profile_image

    return phishing_emails


def add_link_trace(id: str, ip_address: str, user_agent: str):
    data = {
        'ip_address': ip_address,
        'user_agent': user_agent,
        'datetime': datetime.datetime.utcnow()
    }

    DB.get_instance().add_phish_trace(id, data)
