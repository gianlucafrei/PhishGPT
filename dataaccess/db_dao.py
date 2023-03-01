from abc import ABC, abstractmethod


class DbDAO(ABC):

    @abstractmethod
    def is_up(self) -> bool:
        pass

    @abstractmethod
    def add_phish(self, requester: dict, from_api: bool, linkedin_data: dict, profile_image: bytes, openai_request: dict, mail: str):
        pass

    @abstractmethod
    def add_error(self, requester: dict, linkedin_url: str, exception_name: str, exception_message: str):
        pass

    @abstractmethod
    def get_linked_in_data_by_username(self, username: str) -> dict or None:
        pass

    @abstractmethod
    def get_ai_request_response(self) -> list[dict]:
        pass
