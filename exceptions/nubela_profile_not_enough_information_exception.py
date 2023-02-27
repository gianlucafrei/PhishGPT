class NubelaProfileNotEnoughInformationException(Exception):
    def __init__(self):
        self.message = "Not enough profile information to proceed."
        super().__init__(self.message)
