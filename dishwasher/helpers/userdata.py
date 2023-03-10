import json
import time

userlog_event_types = {
    "warns": "Warn",
    "bans": "Ban",
    "kicks": "Kick",
    "tosses": "Toss",
    "notes": "Note",
}


def get_userdata():
    with open("data/userdata.json", "r") as f:
        return json.load(f)


def set_userdata(contents):
    with open("data/userdata.json", "w") as f:
        f.write(contents)


def fill_userdata(userid, uname):
    userdata = get_userdata()
    uid = str(userid)
    if uid not in userdata:
        userdata[uid] = {
            "prefixes": [],
            "timezone": False,
        }
    if uname:
        userdata[uid]["name"] = uname

    return userdata, uid

