from revolt.ext import commands

import config
from helpers.sv_config import get_config
import helpers.errors

def check_if_bot_can_ban(ctx: commands.Context):
    if ctx.server.get_member(ctx.state.me.id).get_permissions().ban_members:
        return True
    else:
        raise helpers.errors.InsufficientBotPermissionsError(["ban_members"])

async def check_if_staff(ctx: commands.Context):
    if ctx.author.id in config.bot_managers:
        return True
    if not ctx.server:
        return False

    if any(
        (
            any(
                r.id == get_config(ctx.server.id, "staff", "staff_role")
                for r in ctx.author.roles
            ),
            any(m == ctx.author.id for m in config.bot_managers),
            ctx.author.get_permissions().manage_server,
        )
    ):
        return True
    else:
        raise helpers.errors.NotStaffError()


async def check_if_bot_manager(ctx: commands.Context):
    if any(m == ctx.author.id for m in config.bot_managers):
        return True
    else:
        raise helpers.errors.NotBotManagerError()


async def check_only_server(ctx: commands.Context):
    if bool(ctx.server is not None):
        return True
    else:
        raise commands.errors.ServerOnly
