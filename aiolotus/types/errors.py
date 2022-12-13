
__all__ = [
    "APIError",
    "fatal_exception",   
]

class APIError(Exception):
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    def __str__(self):
        msg = "[Lotus] {0}: {1}"
        return msg.format(self.status, self.payload)


def fatal_exception(exc):
    if isinstance(exc, APIError):
        # retry on server errors and client errors
        # with 429 status code (rate limited),
        # don't retry on other client errors
        return (400 <= exc.status < 500) and exc.status != 429
    else:
        # retry on all other errors (eg. network)
        return False


