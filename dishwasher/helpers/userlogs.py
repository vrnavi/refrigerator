import json
import os
import time

userlog_event_types = {
    "warns": "Warn",
    "bans": "Ban",
    "kicks": "Kick",
    "tosses": "Toss",
    "notes": "Note",
}


def make_userlog(serverid):
    if not os.path.exists(f"data/userlogs/{serverid}"):
        os.makedirs(f"data/userlogs/{serverid}")
    with open(f"data/userlogs/{serverid}/userlog.json", "w") as f:
        f.write("{}")
        return json.loads("{}")


def get_userlog(serverid):
    with open(f"data/userlogs/{serverid}/userlog.json", "r") as f:
        return json.load(f)


def set_userlog(serverid, contents):
    with open(f"data/userlogs/{serverid}/userlog.json", "w") as f:
        f.write(contents)


def fill_userlog(serverid, userid):
    if os.path.exists(f"data/userlogs/{serverid}/userlog.json"):
        userlogs = get_userlog(serverid)
    else:
        userlogs = make_userlog(serverid)
    uid = str(userid)
    if uid not in userlogs:
        userlogs[uid] = {
            "warns": [],
            "tosses": [],
            "kicks": [],
            "bans": [],
            "notes": [],
            "watch": {"state": False, "thread": None, "message": None},
        }

    return userlogs, uid


def userlog(sid, uid, issuer, reason, event_type):
    userlogs, uid = fill_userlog(sid, uid)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_data = {
        "issuer_id": issuer.id,
        "issuer_name": f"{issuer}",
        "reason": reason,
        "timestamp": timestamp,
    }
    if event_type not in userlogs[uid]:
        userlogs[uid][event_type] = []
    userlogs[uid][event_type].append(log_data)
    set_userlog(sid, json.dumps(userlogs))
    return len(userlogs[uid][event_type])


def setwatch(sid, uid, issuer, watch_state, tracker_thread=None, tracker_msg=None):
    userlogs, uid = fill_userlog(sid, uid)

    userlogs[uid]["watch"] = {
        "state": watch_state,
        "thread": tracker_thread,
        "message": tracker_msg,
    }
    set_userlog(sid, json.dumps(userlogs))
    return
