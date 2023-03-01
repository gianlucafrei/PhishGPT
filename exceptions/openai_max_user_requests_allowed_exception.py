class OpenAiMaxUserRequestsAllowedException(Exception):
    def __init__(self):
        self.message = f"Maximum number of hourly requests to generate mail messages reached. Please wait and try again"
        super().__init__(self.message)
