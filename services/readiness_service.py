from dataaccess import db
from services.helpers import openai_helper, proxycurl_helper


def check(openai_threshold: str, proxycurl_threshold: str):
    is_mongo_up = db.is_up()
    openai_usage = openai_helper.get_usage()
    proxycurl_credit = proxycurl_helper.get_credits()

    state = {
        'mongo_connection': {'value': is_mongo_up},
        'openai_usage': {'value': openai_usage},
        'proxycurl_credit': {'value': proxycurl_credit}
    }

    if not is_mongo_up:
        state['mongo_connection']['error'] = 'Service is down'

    if openai_usage >= float(openai_threshold):
        state['openai_usage']['error'] = 'Payment required'

    if proxycurl_credit <= int(proxycurl_threshold):
        state['proxycurl_credit']['error'] = 'Payment required'

    return state
