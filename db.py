import pymongo


class DB:
    __instance_dict = {}

    def __new__(cls, *args, **kwargs):
        arg_key = str(args) + str(kwargs)
        if arg_key not in cls.__instance_dict:
            cls.__instance_dict[arg_key] = super().__new__(cls)
        return cls.__instance_dict[arg_key]

    def __init__(self, host: str, port: int, db_name: str):
        self.db = pymongo.MongoClient(f"mongodb://{host}:{port}")[db_name]

    def add_session(self, requester: dict, linkedin_data: dict, openai_request: str, mail: str):
        collection = "phish"
        coll = self.db[collection]

        data = {
            "requester": requester,
            "linkedin_data": linkedin_data,
            "openai_request": openai_request,
            "mail": mail
        }

        coll.insert_one(data)
