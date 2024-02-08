ADMINS = []
"""
A list of all the people who get code error notifications.
When DEBUG=False and AdminEmailHandler is configured in LOGGING (done by default),
Django emails these people the details of exceptions raised in the request/response cycle.

Each item in the list should be a tuple of (Full name, email address). Example:

[('John', 'john@example.com'), ('Mary', 'mary@example.com')]
"""

MANAGERS = ADMINS
