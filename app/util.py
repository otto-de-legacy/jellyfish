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


def get_in_dict(key_list, my_dict, default=None):
    tmp = my_dict
    for key in key_list:
        if not isinstance(tmp, dict):
            return default
        tmp = tmp.get(key, default)
    return tmp