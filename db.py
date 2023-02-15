import pymongo


class DB:
    __instance_dict = {}

    def __new__(cls, *args, **kwargs):
        arg_key = str(args) + str(kwargs)
        if arg_key not in cls.__instance_dict:
            cls.__instance_dict[arg_key] = super().__new__(cls)
        return cls.__instance_dict[arg_key]

    def __init__(self, connection: str, db_name: str, user: str, password: str):
        self.db = pymongo.MongoClient(f"{connection}", username=user, password=password)[db_name]

    def add_phish(self, requester: dict, linkedin_data: dict, openai_request: str, mail: str):
        collection = "phishes"
        coll = self.db[collection]

        data = {
            "requester": requester,
            "linkedin_data": linkedin_data,
            "openai_request": openai_request,
            "mail": mail
        }

        coll.insert_one(data)

    def add_error(self, requester: dict, exception_name: str, exception_message: str):
        collection = "errors"
        coll = self.db[collection]

        data = {
            "requester": requester,
            "exception_name": exception_name,
            "exception_message": exception_message,
        }

        coll.insert_one(data)
