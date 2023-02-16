class NubelaAuthException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        self.message = f"Unexpected problem with the API: Status code {status_code}"
        super().__init__(self.message)
