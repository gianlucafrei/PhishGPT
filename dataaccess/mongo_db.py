import datetime
import logging

from pymongo import MongoClient
from bson.objectid import ObjectId
from flatten_dict import flatten

from pymongo.errors import ServerSelectionTimeoutError

from dataaccess.db_dao import DbDAO


class MongoDB(DbDAO):

    def __init__(self, connection: str, db_name: str, user: str, password: str):
        logging.info("Using MongoDB")
        self._db = MongoClient(connection, username=user, password=password)[db_name]

    def is_up(self) -> bool:
        try:
            self._db.client.server_info()
            return True
        except ServerSelectionTimeoutError:
            return False

    def add_phish(self, requester: dict, from_api: bool, linkedin_data: dict, profile_image: bytes, openai_request: dict, subject: str, mail: str) -> str:
        collection = 'phishes'
        coll = self._db[collection]

        data = {
            'requester': requester,
            'from_api': from_api,
            'linkedin_data': linkedin_data,
            'profile_image': profile_image,
            'openai_request': openai_request,
            'subject': subject,
            'mail': mail
        }

        return str(coll.insert_one(data).inserted_id)

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
        logging.info(f"Loading '{username}' from DB")

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
            logging.info(f"'{username}' not found in DB")
            return None, None
        return document['profile_image'], document['linkedin_data']

    def get_ai_request_response(self) -> list[dict]:
        collection = 'phishes'
        coll = self._db[collection]

        projection = {'openai_request.prompt': 1, 'mail': 1, '_id': 0}
        cursor = coll.find({}, projection)

        return list(map(lambda doc: flatten(doc, reducer='dot'), cursor))

    def get_number_of_openai_api_requests_last_hour(self, email: str) -> int:
        collection = 'phishes'
        coll = self._db[collection]

        last_hour_oid = ObjectId.from_datetime(datetime.datetime.utcnow() - datetime.timedelta(hours=1))
        query = {
            '$and': [
                {'requester.email': email},
                {'_id': {'$gte': last_hour_oid}}
            ]
        }

        return coll.count_documents(query)

    def get_number_of_nubela_api_requests_last_hour(self, email: str) -> int:
        collection = 'phishes'
        coll = self._db[collection]

        last_hour_oid = ObjectId.from_datetime(datetime.datetime.utcnow() - datetime.timedelta(hours=1))
        query = {
            '$and': [
                {'requester.email': email},
                {'from_api': True},
                {'_id': {'$gte': last_hour_oid}}
            ]
        }

        return coll.count_documents(query)
    
    def get_previous_phishing_email_generated_by_user(self, email: str) -> list[dict]:
        collection = 'phishes'
        coll = self._db[collection]

        query = {
            'requester.email': email
        }
        projection = {'mail': 1, 'linkedin_data.public_identifier': 1, 'profile_image': 1, 'subject':1}
        cursor = coll.find(query, projection).sort('_id', -1)
        return list(map(lambda doc: flatten(doc, reducer='dot'), cursor))

    def add_phish_trace(self, id: str, data: dict):
        collection = 'phishes'
        coll = self._db[collection]

        coll.update_one(
            {"_id": ObjectId(id)},
            {"$push": {"mail_link_trace": data}}
        )
