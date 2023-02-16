import requests
import json

from exceptions.nubela_auth_exception import NubelaAuthException
from exceptions.nubela_profile_not_found_exception import NubelaProfileNotFoundException


def load_linkedin_data(linkedin_url: str, api_key: str) -> dict:
    print(f"Loading {linkedin_url} from api")

    api_endpoint = 'https://nubela.co/proxycurl/api/v2/linkedin'
    header_dic = {'Authorization': 'Bearer ' + api_key}
    params = {
        'url': linkedin_url,
        'fallback_to_cache': 'on-error',
        'use_cache': 'if-recent'
    }
    response = requests.get(api_endpoint,
                            params=params,
                            headers=header_dic)
    if response.status_code == 200:
        return json.loads(response.content)
    elif response.status_code == 404:
        raise NubelaProfileNotFoundException
    elif response.status_code in (401, 403):
        raise NubelaAuthException(response.status_code)
    else:
        raise Exception(f"Request to Nebula failed with status code {response.status_code}")
