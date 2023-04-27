import config


def get_log_config(gid, ctype):
    return (
        config.guild_configs[gid]["logs"][ctype]
        if config_check(gid, ctype, "logs")
        else None
    )


def get_staff_config(gid, ctype):
    return (
        config.guild_configs[gid]["staff"][ctype]
        if config_check(gid, ctype, "staff")
        else None
    )


def get_toss_config(gid, ctype):
    return (
        config.guild_configs[gid]["toss"][ctype]
        if config_check(gid, ctype, "toss")
        else None
    )


def get_archive_config(gid, ctype):
    return (
        config.guild_configs[gid]["archive"][ctype]
        if config_check(gid, ctype, "archive")
        else None
    )


def get_antiraid_config(gid, ctype):
    return (
        config.guild_configs[gid]["antiraid"][ctype]
        if config_check(gid, ctype, "antiraid")
        else None
    )


def get_surveyr_config(gid, ctype):
    return (
        config.guild_configs[gid]["surveyr"][ctype]
        if config_check(gid, ctype, "surveyr")
        else None
    )


def get_misc_config(gid, ctype):
    return (
        config.guild_configs[gid]["misc"][ctype]
        if config_check(gid, ctype, "misc")
        else None
    )


def config_check(gid, ctype, cid=None):
    # todo: replace with case switch when raspberry pi os upgrades to 3.10 default instead of 3.9
    if ctype == "cotd":
        return (
            gid in config.guild_configs
            and "misc" in config.guild_configs[gid]
            and "cotd_role" in config.guild_configs[gid]["misc"]
            and "cotd_name" in config.guild_configs[gid]["misc"]
        )
    elif ctype == "toss":
        return (
            gid in config.guild_configs
            and "toss" in config.guild_configs[gid]
            and "toss_role" in config.guild_configs[gid]["toss"]
            and "toss_channel" in config.guild_configs[gid]["toss"]
        )
    elif ctype == "antiraid":
        return (
            gid in config.guild_configs
            and "antiraid" in config.guild_configs[gid]
            and "announce_channels" in config.guild_configs[gid]["antiraid"]
            and "mention_threshold" in config.guild_configs[gid]["antiraid"]
            and "join_threshold" in config.guild_configs[gid]["antiraid"]
        )
    elif ctype == "surveyr":
        return (
            gid in config.guild_configs
            and "surveyr" in config.guild_configs[gid]
            and "survey_channel" in config.guild_configs[gid]["surveyr"]
            and "log_types" in config.guild_configs[gid]["surveyr"]
            and "start_case" in config.guild_configs[gid]["surveyr"]
        )
    elif ctype == "archive":
        return (
            gid in config.guild_configs
            and "archive" in config.guild_configs[gid]
            and "drive_folder" in config.guild_configs[gid]["archive"]
            and "unroleban_expiry" in config.guild_configs[gid]["archive"]
        )
    else:
        return (
            gid in config.guild_configs
            and cid in config.guild_configs[gid]
            and ctype in config.guild_configs[gid][cid]
        )
