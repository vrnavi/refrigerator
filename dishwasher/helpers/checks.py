import config


def check_if_staff(ctx):
    if not ctx.guild or ctx.guild.id not in config.guild_configs:
        return False
    return any(
        r.id == config.guild_configs[ctx.guild.id]["staff"]["staff_role"]
        for r in ctx.author.roles
    )


def check_if_bot_manager(ctx):
    return any(m == ctx.author.id for m in config.bot_managers)
