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

    def add_phish(self, requester: dict, from_api: bool, linkedin_data: dict, profile_image: bytes, openai_request: dict, subject: str, mail: str) -> str:
        return self._db_type.add_phish(requester, from_api, linkedin_data, profile_image, openai_request, subject, mail)

    def add_error(self, requester: dict, linkedin_url: str, exception_name: str, exception_message: str):
        self._db_type.add_error(requester, linkedin_url, exception_name, exception_message)

    def get_linked_in_data_by_username(self, username: str) -> dict or None:
        return self._db_type.get_linked_in_data_by_username(username)

    def get_ai_request_response(self) -> list[dict]:
        return self._db_type.get_ai_request_response()

    def get_number_of_openai_api_requests_last_hour(self, email: str) -> int:
        return self._db_type.get_number_of_openai_api_requests_last_hour(email)

    def get_number_of_nubela_api_requests_last_hour(self, email: str) -> int:
        return self._db_type.get_number_of_nubela_api_requests_last_hour(email)

    def add_phish_trace(self, id: str, data: dict):
        self._db_type.add_phish_trace(id, data)
