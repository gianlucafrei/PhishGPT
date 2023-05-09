from dataaccess.DB import DB
from services.helpers import proxycurl_helper


def check(proxycurl_threshold: str) -> dict:
    is_mongo_up = DB.get_instance().is_up()
    proxycurl_credit = proxycurl_helper.get_credits()

    state = {
        'mongo_connection': {'value': is_mongo_up},
        'proxycurl_credit': {'value': proxycurl_credit}
    }

    if not is_mongo_up:
        state['mongo_connection']['error'] = 'Service is down'

    if proxycurl_credit <= int(proxycurl_threshold):
        state['proxycurl_credit']['error'] = 'Payment required'

    return state
