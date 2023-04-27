import config


def get_log_config(gid, cfg_type):
    return (
        config.guild_configs[gid]["logs"][cfg_type]
        if config_check(gid, cfg_type, "logs")
        else None
    )


def get_staff_config(gid, cfg_type):
    return (
        config.guild_configs[gid]["staff"][cfg_type]
        if config_check(gid, cfg_type, "staff")
        else None
    )


def get_toss_config(gid, cfg_type):
    return (
        config.guild_configs[gid]["toss"][cfg_type]
        if config_check(gid, cfg_type, "toss")
        else None
    )


def get_archive_config(gid, cfg_type):
    return (
        config.guild_configs[gid]["archive"][cfg_type]
        if config_check(gid, cfg_type, "archive")
        else None
    )


def get_antiraid_config(gid, cfg_type):
    return (
        config.guild_configs[gid]["antiraid"][cfg_type]
        if config_check(gid, cfg_type, "antiraid")
        else None
    )


def get_misc_config(gid, cfg_type):
    return (
        config.guild_configs[gid]["misc"][cfg_type]
        if config_check(gid, cfg_type, "misc")
        else None
    )


def config_check(gid, ctype, cid=None):
    match ctype:
        case "cotd":
            return (
                gid in config.guild_configs
                and "cotd" in config.guild_configs[gid]
                and "cotd_role" in config.guild_configs[gid][cid]
                and "cotd_name" in config.guild_configs[gid][cid]
            )
        case _:
            return (
                gid in config.guild_configs
                and cid in config.guild_configs[gid]
                and ctype in config.guild_configs[gid][cid]
            )
