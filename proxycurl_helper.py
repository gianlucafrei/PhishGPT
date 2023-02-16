import requests
import json
import os

from exceptions.nubela_auth_exception import NubelaAuthException
from exceptions.nubela_profile_not_found_exception import NubelaProfileNotFoundException

cache_folder_name = "./cache"


def load_linkedin_data_with_cache(linkedin_url: str, api_key: str):

    if not os.path.exists(cache_folder_name):
        os.mkdir(cache_folder_name)

    profile_name = linkedin_url[linkedin_url.rfind("/"):]
    file_name = cache_folder_name + "/" + profile_name + ".json"

    if not os.path.exists(file_name):
        # Create the file if it doesn't exist

        print(f"Loading {linkedin_url} from API")
        result = load_linkedin_data(linkedin_url, api_key)
        
        with open(file_name, "w") as file:
            result_json = json.dumps(result)
            file.write(result_json)
        return result
    else:

        print(f"Loading {linkedin_url} from cache")
        with open(file_name, "r") as file:
            result_json = file.read()
            result = json.loads(result_json)
        return result
    

def load_linkedin_data(linkedin_url: str, api_key: str):

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

    # Check if the response status code is 200 (OK)
    if response.status_code == 200:
        # Deserialize the response content as a JSON string
        json_data = json.loads(response.content)
        # Do something with the JSON data
        return json_data
    elif response.status_code == 404:
        raise NubelaProfileNotFoundException
    elif response.status_code in (401, 403):
        raise NubelaAuthException(response.status_code)
    else:
        # Handle non-200 response status codes
        raise Exception(f"Request to Nebula failed with status code {response.status_code}")
