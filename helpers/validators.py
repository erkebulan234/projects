import re

def is_valid_email(email):
    """Проверка формата email"""
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    return re.match(regex, email, re.IGNORECASE)

__all__ = ['is_valid_email']