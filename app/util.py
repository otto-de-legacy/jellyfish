import json

from app import config
from functools import reduce


def load_app(app_id):
    raw_app = config.rdb.get(app_id)
    if raw_app:
        return json.loads(raw_app.decode())
    return None


def get_by_list(dic, keys):
    return reduce(dict.get, keys, dic)
