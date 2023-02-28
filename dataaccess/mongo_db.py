from pymongo import MongoClient
from bson.objectid import ObjectId
from flatten_dict import flatten
import datetime

from pymongo.errors import ServerSelectionTimeoutError

from dataaccess.db_dao import DbDAO


class MongoDB(DbDAO):

    def __init__(self, connection: str, db_name: str, user: str, password: str):
        self._db = MongoClient(connection, username=user, password=password)[db_name]

    def is_up(self) -> bool:
        try:
            self._db.client.server_info()
            return True
        except ServerSelectionTimeoutError:
            return False

    def add_phish(self, requester: dict, from_api: bool, linkedin_data: dict, profile_image: bytes, openai_request: dict, mail: str):
        collection = 'phishes'
        coll = self._db[collection]

        data = {
            'requester': requester,
            'from_api': from_api,
            'linkedin_data': linkedin_data,
            'profile_image': profile_image,
            'openai_request': openai_request,
            'mail': mail
        }

        coll.insert_one(data)

    def add_error(self, requester: dict, linkedin_url: str, exception_name: str, exception_message: str):
        collection = 'errors'
        coll = self._db[collection]

        data = {
            'requester': requester,
            'linkedin_url': linkedin_url,
            'exception_name': exception_name,
            'exception_message': exception_message,
        }

        coll.insert_one(data)

    def get_linked_in_data_by_username(self, username: str) -> dict or None:
        print(f"Loading '{username}' from DB")

        collection = 'phishes'
        coll = self._db[collection]

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

    def get_ai_request_response(self) -> list[dict]:
        collection = 'phishes'
        coll = self._db[collection]

        projection = {'openai_request.prompt': 1, 'mail': 1, '_id': 0}
        cursor = coll.find({}, projection)

        return list(map(lambda doc: flatten(doc, reducer='dot'), cursor))
