from pymongo import MongoClient


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
