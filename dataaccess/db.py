from pymongo import MongoClient
from bson.objectid import ObjectId
from flatten_dict import flatten
import datetime

from pymongo.errors import ServerSelectionTimeoutError

db: MongoClient


def connect(connection: str, db_name: str, user: str, password: str):
    global db
    db = MongoClient(connection, username=user, password=password)[db_name]


def is_up() -> bool:
    try:
        db.client.server_info()
        return True
    except ServerSelectionTimeoutError:
        return False


def add_phish(requester: dict, from_api: bool, linkedin_data: dict, profile_image: bytes, openai_request: dict, mail: str):
    collection = 'phishes'
    coll = db[collection]

    data = {
        'requester': requester,
        'from_api': from_api,
        'linkedin_data': linkedin_data,
        'profile_image': profile_image,
        'openai_request': openai_request,
        'mail': mail
    }

    coll.insert_one(data)


def add_error(requester: dict, linkedin_url: str, exception_name: str, exception_message: str):
    collection = 'errors'
    coll = db[collection]

    data = {
        'requester': requester,
        'linkedin_url': linkedin_url,
        'exception_name': exception_name,
        'exception_message': exception_message,
    }

    coll.insert_one(data)


def get_linked_in_data_by_username(username: str) -> dict or None:
    print(f"Loading '{username}' from DB")

    collection = 'phishes'
    coll = db[collection]

    last_week_oid = ObjectId.from_datetime(datetime.datetime.utcnow() - datetime.timedelta(days=7))
    query = {
        '$and': [
            {'linkedin_data.public_identifier': username},
            {'from_api': True},
            {'_id': {'$gte': last_week_oid}}
        ]
    }

    document = coll.find_one(query)
    if not document:
        print(f"'{username}' not found in DB")
        return None, None
    return document['profile_image'], document['linkedin_data']


def get_ai_request_response():
    collection = 'phishes'
    coll = db[collection]

    projection = {'openai_request.prompt': 1, 'mail': 1, '_id': 0}
    cursor = coll.find({}, projection)

    return map(lambda doc: flatten(doc, reducer='dot'), cursor)
