import json
import os
import time

stock_configs = {
    "logs": {
        "mlog_thread": None,
        "slog_thread": None,
        "ulog_thread": None,
    },
    "staff": {
        "staff_role": None,
        "exstaff_role": None,
        "staff_channel": None,
        "rules_url": None,
        "appeal_url": None,
        "ban_appeal_channel": None,
        "ban_appeal_webhook_id": None,
        "tracker_channel": None,
    },
    "toss": {
        "enable": False,
        "toss_role": None,
        "toss_channel": None,
        "toss_channels": None,
    },
    "archive": {
        "enable": False,
        "drive_folder": None,
        "unroleban_expiry": None,
    },
    "antiraid": {
        "enable": False,
        "announce_channels": None,
        "mention_threshold": None,
        "join_threshold": None,
    },
    "surveyr": {
        "enable": False,
        "survey_channel": None,
        "log_types": None,
        "start_case": None,
    },
    "cotd": {
        "enable": False,
        "cotd_role": None,
        "cotd_name": None,
    },
    "misc": {
        "authorized_roles": None,
        "bot_roles": None,
        "cotd_role": None,
        "cotd_name": None,
        "embed_enable": False,
        "translate_enable": False,
        "burstreacts_enable": False,
    },
}
server_data = "data/servers"


def make_config(sid):
    if not os.path.exists(f"{server_data}/{sid}"):
        os.makedirs(f"{server_data}/{sid}")
    with open(f"{server_data}/{sid}/config.json", "w") as f:
        f.write(str(stock_configs))
        return stock_configs


def get_raw_config(sid):
    with open(f"{server_data}/{sid}/config.json", "r") as f:
        return json.load(f)


def set_raw_config(sid, contents):
    with open(f"{server_data}/{sid}/config.json", "w") as f:
        f.write(contents)


def get_config(sid, part, key):
    configs = fill_config(sid)

    if part not in configs or key not in configs[part]:
        configs = set_config(sid, part, key, stock_configs[part][key])

    return configs[part][key]


def set_config(sid, part, key, value):
    configs = fill_config(sid)

    if part not in configs:
        configs[part] = {}
    configs[part][key] = value

    set_raw_config(sid, json.dumps(configs))
    return configs


def fill_config(sid):
    configs = (
        get_raw_config(sid)
        if os.path.exists(f"{server_data}/{sid}/config.json")
        else make_config(sid)
    )

    return configs
