from unidecode import unidecode
import revolt
from revolt.ext import commands

from helpers.checks import check_if_staff, check_only_server


class NameCheck(commands.Cog):
    """
    Keeping names readable.
    """

    def __init__(self, bot: commands.CommandsClient):
        self.bot = bot
        self.readablereq = 1

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def decancer(self, ctx: commands.Context, target: commands.MemberConverter):
        oldname = target.name
        newname = unidecode(target.name)
        if not newname:
            newname = "Unreadable Name"
        await self._edit_nickname(ctx.server, target, newname)
        return await ctx.message.reply(
            f"Successfully decancered **{oldname}** to `{newname}`.",
            mention=False,
        )

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def dehoist(self, ctx: commands.Context, target: commands.MemberConverter):
        oldname = target.name
        await self._edit_nickname(ctx.server, target, "᲼" + target.name)
        return await ctx.message.reply(
            f"Successfully dehoisted **{oldname}**.", mention=False
        )

    async def _edit_nickname(
        self, server: revolt.Server, member: revolt.Member, nickname: str = None
    ) -> None:
        """
        Monkey-patch of `ctx.author.edit` since it having
        400 (bad request) HTTP error when tring to edit something.
        """
        if nickname:
            await self.bot.http.request(
                "PATCH",
                f"/servers/{server.id}/members/{member.id}",
                json={"remove": None, "nickname": nickname},
            )
        else:
            await self.bot.http.request(
                "PATCH",
                f"/servers/{server.id}/members/{member.id}",
                json={"remove": ["Nickname"], "nickname": None},
            )

    # FIXME: revolt.py on_member_join event handling?
    """
    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if not get_config(member.guild.id, "misc", "autoreadable_enable"):
            return

        name = member.display_name

        # Non-Alphanumeric
        readable = len([b for b in name if b.isascii()])
        if readable < self.readablereq:
            name = unidecode(name) if unidecode(name) else "Unreadable Name"

        # Hoist
        if name[:1] in ("!", "-", ".", "(", ")", ":"):
            name = "᲼" + name

        # Validate
        if name != member.display_name:
            await member.edit(nick=name, reason="Automatic Namecheck")

    @Cog.listener()
    async def on_member_update(self, member_before, member_after):
        await self.bot.wait_until_ready()
        if not get_config(member_after.guild.id, "misc", "autoreadable_enable"):
            return

        name = member_after.display_name

        # Non-Alphanumeric
        readable = len([b for b in name if b.isascii()])
        if readable < self.readablereq:
            name = unidecode(name) if unidecode(name) else "Unreadable Name"

        # Hoist
        if name[:1] in ("!", "-", ".", "(", ")", ":"):
            name = "᲼" + name

        # Validate
        if name != member_after.display_name:
            await member_after.edit(nick=name, reason="Automatic Namecheck")
    """


def setup(bot: commands.CommandsClient):
    return NameCheck(bot)
