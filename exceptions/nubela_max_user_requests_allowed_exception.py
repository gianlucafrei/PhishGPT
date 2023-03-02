class NubelaMaxUserRequestsAllowedException(Exception):
    def __init__(self):
        self.message = f"Maximum number of hourly requests to retrieve user information reached. Please wait and try again"
        super().__init__(self.message)
