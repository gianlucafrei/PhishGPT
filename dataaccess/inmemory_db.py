from dataaccess.db_dao import DbDAO


class InMemoryDB(DbDAO):

    def __init__(self):
        print("Using in-memory DB")
        self._db = {}

    def is_up(self) -> bool:
        return True

    def add_phish(self, requester: dict, from_api: bool, linkedin_data: dict, profile_image: bytes, openai_request: dict, subject: str, mail: str) -> str:
        collection = 'phishes'

        data = {
            'requester': requester,
            'from_api': from_api,
            'linkedin_data': linkedin_data,
            'profile_image': profile_image,
            'openai_request': openai_request,
            'subject': subject,
            'mail': mail
        }

        self._db.setdefault(collection, []).append(data)

        return str(len(self._db[collection]))

    def add_error(self, requester: dict, linkedin_url: str, exception_name: str, exception_message: str):
        collection = 'errors'

        data = {
            'requester': requester,
            'linkedin_url': linkedin_url,
            'exception_name': exception_name,
            'exception_message': exception_message,
        }

        self._db.setdefault(collection, []).append(data)

    def get_linked_in_data_by_username(self, username: str) -> dict or None:
        print(f"Loading '{username}' from DB")

        collection = 'phishes'

        documents = list(filter(lambda doc: doc['from_api'] and doc['linkedin_data']['public_identifier'] == username,
                                self._db.get(collection, [])))

        if not any(documents):
            print(f"'{username}' not found in DB")
            return None, None

        document = documents[0]
        return document['profile_image'], document['linkedin_data']

    def get_ai_request_response(self) -> list[dict]:
        collection = 'phishes'

        return list(map(lambda doc: {'openai_request.prompt': doc['openai_request']['prompt'], 'mail': doc['mail']},
                        self._db.get(collection, [])))

    def get_number_of_openai_api_requests_last_hour(self, email: str) -> int:
        collection = 'phishes'

        documents = list(filter(lambda doc: doc['requester']['email'] == email,
                                self._db.get(collection, [])))

        return len(documents)

    def get_number_of_nubela_api_requests_last_hour(self, email: str) -> int:
        collection = 'phishes'

        documents = list(filter(lambda doc: doc['from_api'] and doc['requester']['email'] == email,
                                self._db.get(collection, [])))

        return len(documents)

    def add_phish_trace(self, id: str, data: dict):
        collection = 'phishes'

        self._db[collection][int(id) - 1].setdefault('mail_link_trace', []).append(data)
