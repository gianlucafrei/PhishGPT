from dataaccess.db_dao import DbDAO


class DB(DbDAO):

    __instance = None

    def __init__(self):
        self._db_type = None
        if DB.__instance is not None:
            raise Exception("DB class is singleton.")
        else:
            DB.__instance = self

    @staticmethod
    def get_instance() -> 'DB':
        if DB.__instance is None:
            DB()
        return DB.__instance

    def set_db_type(self, db_type: DbDAO):
        self._db_type = db_type

    def is_up(self) -> bool:
        return self._db_type.is_up()

    def add_phish(self, requester: dict, from_api: bool, linkedin_data: dict, profile_image: bytes, openai_request: dict, mail: str):
        self._db_type.add_phish(requester, from_api, linkedin_data, profile_image, openai_request, mail)

    def add_error(self, requester: dict, linkedin_url: str, exception_name: str, exception_message: str):
        self._db_type.add_error(requester, linkedin_url, exception_name, exception_message)

    def get_linked_in_data_by_username(self, username: str) -> dict or None:
        return self._db_type.get_linked_in_data_by_username(username)

    def get_ai_request_response(self) -> list[dict]:
        return self._db_type.get_ai_request_response()
