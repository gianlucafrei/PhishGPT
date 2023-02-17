class NubelaProfileNotFoundException(Exception):
    def __init__(self):
        self.message = "Profile not found. This may occur when the profile does not exist, is private or you provided a company one"
        super().__init__(self.message)
