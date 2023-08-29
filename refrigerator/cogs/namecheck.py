from unidecode import unidecode
import revolt
from revolt.ext import commands
from helpers.sv_config import get_config

from helpers.checks import check_if_staff, check_only_server


class NameCheck(commands.Cog):
    """
    Keeping names readable.
    """

    def __init__(self, bot: commands.CommandsClient):
        self.bot = bot
        self.bot.on_member_join_listeners.append(self.on_member_join)
        self.bot.on_member_update_listeners.append(self.on_member_update)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def decancer(self, ctx: commands.Context, target: commands.MemberConverter):
        oldname = target.name
        newname = unidecode(target.name)
        if not newname:
            newname = "Unreadable Name"
        await target.edit(nickname=newname)
        return await ctx.message.reply(
            f"Successfully decancered **{oldname}** to `{newname}`.",
            mention=False,
        )

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def dehoist(self, ctx: commands.Context, target: commands.MemberConverter):
        oldname = target.name
        await target.edit(nickname=f"\u1cbc{target.name}")
        return await ctx.message.reply(
            f"Successfully dehoisted **{oldname}**.", mention=False
        )

    async def on_member_join(self, member: revolt.Member):
        if not get_config(member.server.id, "misc", "autoreadable_enable"):
            return

        name = member.name

        # Non-Alphanumeric
        readable = len([b for b in name if b.isascii()])
        if readable / len(name) < 2 / 3: # at least 2/3 of the name must be readable
            name = unidecode(name) if unidecode(name) else "Unreadable Name"

        # Hoist
        if any(name.startswith(c) for c in ("!", "-", ".", "(", ")", ":")):
            name = f"\u1cbc{name}"

        # Validate
        if name != member.name:
            await member.edit(nickname=name)

    async def on_member_update(self, member_before: revolt.Member, member_after: revolt.Member):
        if not get_config(member_after.server.id, "misc", "autoreadable_enable"):
            return

        name = member_after.name

        # Non-Alphanumeric
        readable = len([b for b in name if b.isascii()])
        if readable / len(name) < 2 / 3: # at least 2/3 of the name must be readable
            name = unidecode(name) if unidecode(name) else "Unreadable Name"

        # Hoist
        if any(name.startswith(c) for c in ("!", "-", ".", "(", ")", ":")):
            name = f"\u1cbc{name}"

        # Validate
        if name != member_after.name:
            await member_after.edit(nickname=name)


def setup(bot: commands.CommandsClient):
    return NameCheck(bot)
