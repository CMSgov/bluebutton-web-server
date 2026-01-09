import hashlib
import os
import requests


def hash(s):
    shake = hashlib.shake_128(f'{s}'.encode('utf-8'))
    # Use 64 bits of the 128-bit hash. Make sure we're signed, or it
    # won't fit in the 64-bit signed range in the DB.
    h = int.from_bytes(shake.digest(8), 'big', signed=True)
    return str(h)


def salt(s):
    salt = os.getenv("ITSLOG_SALT")
    if salt is None:
        raise Exception()
    shake = hashlib.shake_128(f'{s}/{salt}'.encode('utf-8'))
    h = int.from_bytes(shake.digest(8), 'big', signed=True)
    return str(h)


class ItsLog:
    base = os.getenv("ITSLOG_API_BASE")

    @staticmethod
    def _put(url):
        requests.put(url, verify=False, headers={"x-api-key": os.getenv("ITSLOG_API_KEY")})

    @staticmethod
    def se(source, event):
        ItsLog._put(f"{ItsLog.base}/v1/se/" + "/".join(map(hash, [source, event])))

    def sev(source, event, value):
        ItsLog._put(f"{ItsLog.base}/v1/se/" + "/".join(map(hash, [source, event])) + salt(value))
