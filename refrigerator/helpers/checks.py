from revolt.ext import commands

import config
from helpers.sv_config import get_config


async def check_if_staff(ctx: commands.Context):
    if ctx.author.id in config.bot_managers:
        return True
    if not ctx.server:
        return False

    return any(
        (
            any(
                r.id == get_config(ctx.guild.id, "staff", "staff_role")
                for r in ctx.author.roles
            ),
            any(m == ctx.author.id for m in config.bot_managers),
            ctx.author.get_permissions().manage_server,
        )
    )


async def check_if_bot_manager(ctx: commands.Context):
    return any(m == ctx.author.id for m in config.bot_managers)


async def check_only_server(ctx: commands.Context):
    return bool(ctx.server is not None)
