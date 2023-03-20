import json
import time


def get_userdata():
    with open("data/userdata.json", "r") as f:
        return json.load(f)


def get_userprefix(uid):
    userdata = get_userdata()
    uid = str(uid)
    if uid not in userdata:
        return None
    return userdata[uid]["prefixes"]


def set_userdata(contents):
    with open("data/userdata.json", "w") as f:
        f.write(contents)


def fill_userdata(userid):
    userdata = get_userdata()
    uid = str(userid)
    if uid not in userdata:
        userdata[uid] = {
            "prefixes": [],
            "timezone": False,
        }
    return userdata, uid
