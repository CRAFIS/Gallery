import hashlib

def auth(user, password):
    if user and str.isalnum(password):
        digest = getHash(password + user["salt"])
        if user["hashed_password"] == digest:
            return True
    return False

def getHash(password):
    text = password.encode("utf-8")
    result = hashlib.sha512(text).hexdigest()
    return result
