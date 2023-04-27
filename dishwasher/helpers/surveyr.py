import json
import os
import time

surveyr_event_types = {
    "bans": "Ban",
    "kicks": "Kick",
}


def make_surveys(serverid):
    if not os.path.exists(f"data/userlogs/{serverid}"):
        os.makedirs(f"data/userlogs/{serverid}")
    with open(f"data/userlogs/{serverid}/surveys.json", "w") as f:
        f.write("{}")
    return json.loads("{}")


def get_surveys(serverid):
    with open(f"data/userlogs/{serverid}/surveys.json", "r") as f:
        return json.load(f)


def set_surveys(serverid, contents):
    with open(f"data/userlogs/{serverid}/surveys.json", "w") as f:
        f.write(contents)


def new_survey(sid, uid, mid, issuer, reason, event):
    surveys = (
        get_surveys(sid)
        if os.path.exists(f"data/userlogs/{sid}/surveys.json")
        else make_surveys(sid)
    )

    cid = int(dict.keys()[-1]) + 1

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    sv_data = {
        "type": event,
        "reason": reason,
        "timestamp": timestamp,
        "target_id": uid,
        "issuer_id": issuer.id,
        "post_id": mid,
    }
    surveys[str(cid)] = sv_data
    set_surveys(sid, json.dumps(surveys))
    return len(surveys)


def edit_survey(sid, cid, issuer, reason, event):
    survey = get_surveys(sid)[str(cid)]

    sv_data = {
        "type": event,
        "reason": reason,
        "issuer_id": issuer.id,
    }
    for k, v in sv_data:
        surveys[str(cid)][k] = log_data[v]
    set_surveys(sid, json.dumps(surveys))
    return len(surveys)
