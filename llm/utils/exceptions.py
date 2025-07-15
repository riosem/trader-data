class SendAssistantMessageException(Exception):
    def __init__(self, message):
        self.message = message
        self.code = 500
        super().__init__(self.message)