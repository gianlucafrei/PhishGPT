from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime


class DB:
    __instance_dict = {}

    def __new__(cls, *args, **kwargs):
        arg_key = str(args) + str(kwargs)
        if arg_key not in cls.__instance_dict:
            cls.__instance_dict[arg_key] = super().__new__(cls)
        return cls.__instance_dict[arg_key]

    def __init__(self, connection: str, db_name: str, user: str, password: str):
        self.db = MongoClient(f"{connection}", username=user, password=password)[db_name]

    def add_phish(self, requester: dict, from_api: bool, linkedin_data: dict, openai_request: dict, mail: str):
        collection = "phishes"
        coll = self.db[collection]

        data = {
            "requester": requester,
            "from_api": from_api,
            "linkedin_data": linkedin_data,
            "openai_request": openai_request,
            "mail": mail
        }

        coll.insert_one(data)

    def add_error(self, requester: dict, linkedin_url: str, exception_name: str, exception_message: str):
        collection = "errors"
        coll = self.db[collection]

        data = {
            "requester": requester,
            "linkedin_url": linkedin_url,
            "exception_name": exception_name,
            "exception_message": exception_message,
        }

        coll.insert_one(data)

    def get_linked_in_data_by_username(self, username: str) -> dict or None:
        print(f"Loading '{username}' from DB")

        collection = "phishes"
        coll = self.db[collection]

        last_week_oid = ObjectId.from_datetime(datetime.datetime.utcnow() - datetime.timedelta(days=7))
        query = {
            "$and": [
                {"linkedin_data.public_identifier": username},
                {"from_api": True},
                {"_id": {"$gte": last_week_oid}}
            ]
        }

        select_field = 'linkedin_data'
        document = coll.find_one(query, {select_field: 1})
        if not document:
            print(f"'{username}' not found in DB")
            return None
        return document[select_field]

    def get_all_generated_mail(self):
        collection = "phishes"
        coll = self.db[collection]

        projection = { 'openai_request.prompt': 1, 'mail': 1, '_id': 0 }
        cursor = coll.find({}, projection)
        
        result = []
        for doc in cursor:
            new_doc = {}
            for key, value in doc.items():
                if isinstance(value, dict):
                    for nested_key, nested_value in value.items():
                        new_doc[f"{key}.{nested_key}"] = nested_value
                else:
                    new_doc[key] = value
            result.append(new_doc)
        
        return result
