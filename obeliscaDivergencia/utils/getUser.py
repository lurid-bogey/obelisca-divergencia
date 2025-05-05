import os

# A unique identifier representing your end-user, which can help to monitor and detect abuse.
USER_NAME = os.environ.get('USERNAME', '').lower()
