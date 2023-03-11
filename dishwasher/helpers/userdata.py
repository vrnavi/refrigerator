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

def get_userprefix(uid):
    userdata = get_userdata()
    uid = str(uid)
    if uid not in userdata:
        return None
    return userdata[uid]["prefixes"]
    

def set_userdata(contents):
    try:
        with open("data/userdata.json", "w") as f:
            f.write(contents)
    except:
        print("Unable to write contents")
        print(contents) 


def fill_userdata(userid, uname = None):
    userdata = get_userdata()
    uid = str(userid)
    if uid not in userdata:
        userdata[uid] = {
            "prefixes": [],
            "timezone": False,
        }
    return userdata, uid

