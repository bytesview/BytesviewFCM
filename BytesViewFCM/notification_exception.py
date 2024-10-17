
class NotificationException(Exception):
    """Base class for all other exceptions"""

    def __init__(self, Error):
        self.Error = Error

class TableNotExistError(NotificationException):
    def __init__(self, error):
        super().__init__(error)

class RateLimitExceeded(NotificationException):
    def __init__(self, error):
        super().__init__(error)