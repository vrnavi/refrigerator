import json
import os
import datetime
import config

surveyr_event_types = {
    "bans": "Ban",
    "kicks": "Kick",
    "softbans": "Softban",
}


def make_surveys(serverid):
    if not os.path.exists(f"data/userlogs/{serverid}"):
        os.makedirs(f"data/userlogs/{serverid}")
    with open(f"data/userlogs/{serverid}/surveys.json", "w") as f:
        f.write("{}")
    return json.loads("{}")


def get_surveys(serverid):
    if not os.path.exists(f"data/userlogs/{serverid}/userlog.json"):
        userlogs = make_userlog(serverid)
    with open(f"data/userlogs/{serverid}/surveys.json", "r") as f:
        return json.load(f)


def set_surveys(serverid, contents):
    with open(f"data/userlogs/{serverid}/surveys.json", "w") as f:
        f.write(contents)


def new_survey(sid, uid, mid, iid, reason, event):
    surveys = (
        get_surveys(sid)
        if os.path.exists(f"data/userlogs/{sid}/surveys.json")
        else make_surveys(sid)
    )

    cid = (
        config.guild_configs[sid]["surveyr"]["start_case"]
        if len(surveys.keys()) == 0
        else int(list(surveys)[-1]) + 1
    )

    timestamp = int(datetime.datetime.now().timestamp())
    sv_data = {
        "type": event,
        "reason": reason,
        "timestamp": timestamp,
        "target_id": uid,
        "issuer_id": iid,
        "post_id": mid,
    }
    surveys[str(cid)] = sv_data
    set_surveys(sid, json.dumps(surveys))
    return cid, timestamp


def edit_survey(sid, cid, iid, reason, event):
    survey = get_surveys(sid)

    sv_data = {
        "type": event,
        "reason": reason,
        "issuer_id": iid,
    }
    for k, v in sv_data.items():
        survey[str(cid)][k] = v
    set_surveys(sid, json.dumps(survey))
    return cid
