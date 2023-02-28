from dataaccess.db_dao import DbDAO


class InMemoryDB(DbDAO):

    __instance = None

    def __init__(self, db_name: str):
        self._db = {}

    def is_up(self) -> bool:
        return True

    def add_phish(self, requester: dict, from_api: bool, linkedin_data: dict, profile_image: bytes, openai_request: dict, mail: str):
        pass

    def add_error(self, requester: dict, linkedin_url: str, exception_name: str, exception_message: str):
        pass

    def get_linked_in_data_by_username(self, username: str) -> dict or None:
        pass

    def get_ai_request_response(self) -> list[dict]:
        pass
