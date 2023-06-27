import revolt
from revolt.ext import commands

from helpers.checks import check_only_server
from helpers.sv_config import get_config


class CogOneShot(commands.Cog):
    def __init__(self, bot: commands.CommandsClient):
        self.qualified_name = "oneshot"
        self.bot = bot

    @commands.check(check_only_server)
    @commands.command(aliases=["renavi"])
    async def ren(self, ctx: commands.Context):
        """[U] What does Dishwasher think about ren?"""
        await ctx.send("HELP! HELP! HELP!")

    @commands.check(check_only_server)
    @commands.command()
    async def staff(self, ctx: commands.Context):
        """[U] Shows currently active staff."""
        staff_role = ctx.server.get_role(
            get_config(ctx.server.id, "staff", "staff_role")
        )

        # revolt.py does not have `Role.get_members()`... ;-;
        staff_members = []
        for m in ctx.server.members:
            for r in m.roles:
                if r.id == staff_role.id:
                    staff_members.append(m)

        embed = revolt.SendableEmbed(
            title="🛠️ Staff List",
            description=f"Voting requirement is `{int(len(staff_members)/2//1+1)}`.\n\n",
            colour=staff_role.color,
        )

        online = []
        away = []
        focus = []
        dnd = []
        offline = []

        for m in staff_members:
            u = f"{m.mention}"

            if m.bot:
                # Bots don't have statuses
                if m.online:
                    online.append(u)
                else:
                    offline.append(u)
            else:
                if m.status.presence.value == "Online":
                    online.append(u)
                elif m.status.presence.value == "Idle":
                    away.append(u)
                elif m.status.presence.value == "Focus":
                    focus.append(u)
                elif m.status.presence.value == "Busy":
                    dnd.append(u)
                else:
                    offline.append(u)

        if online:
            embed.description += (
                f"### 🟢 Online [`{len(online)}`/`{len(staff_members)}`]\n"
                f"{', '.join(online)}"
                "\n"
            )
        if focus:
            embed.description += (
                f"### 🔵 Focus [`{len(focus)}`/`{len(staff_members)}`]\n"
                f"{', '.join(focus)}"
                "\n"
            )
        if away:
            embed.description += (
                f"### 🟡 Idle [`{len(away)}`/`{len(staff_members)}`]\n"
                f"{', '.join(away)}"
                "\n"
            )
        if dnd:
            embed.description += (
                f"### 🔴 Do Not Disturb [`{len(dnd)}`/`{len(staff_members)}`]\n"
                f"{', '.join(dnd)}"
                "\n"
            )
        if offline:
            embed.description += (
                f"### ⚫ Offline [`{len(offline)}`/`{len(staff_members)}`]\n"
                f"{', '.join(offline)}"
                "\n"
            )

        await ctx.message.reply(embed=embed, mention=False)

    @commands.check(check_only_server)
    @commands.command(aliases=["pingmods", "summonmods", "modping"])
    async def pingmod(self, ctx: commands.Context):
        """[U] Pings mods, only use when there's an emergency."""
        staff_role = ctx.server.get_role(
            get_config(ctx.server.id, "staff", "staff_role")
        )

        # The hell in Revolt you CAN'T ping roles!? Awoo! - hat_kid
        staff_members = []
        for m in ctx.server.members:
            for r in m.roles:
                if r.id == staff_role.id:
                    staff_members.append(m)

        await ctx.message.reply(
            f"{', '.join([s.mention for s in staff_members])}\n"
            f"## {ctx.author.name} is requesting assistance.",
            mention=False,
        )

    @commands.check(check_only_server)
    @commands.command(aliases=["togglemod"])
    async def modtoggle(self, ctx: commands.Context):
        """[S] Toggles your Staff role.

        If you have Staff, it will replace it with Ex-Staff, and vice versa."""
        staff_role = ctx.server.get_role(
            get_config(ctx.server.id, "staff", "staff_role")
        )
        exstaff_role = ctx.server.get_role(
            get_config(ctx.server.id, "staff", "exstaff_role")
        )
        if staff_role in ctx.author.roles:
            roles = ctx.author.roles
            roles.remove(staff_role)
            roles.append(exstaff_role)
            await self._edit_roles(ctx.server, ctx.author, [r.id for r in roles])
            await ctx.message.reply("`🔴 Staff`", mention=False)
        elif exstaff_role in ctx.author.roles:
            roles = ctx.author.roles
            roles.remove(exstaff_role)
            roles.append(staff_role)
            await self._edit_roles(ctx.server, ctx.author, [r.id for r in roles])
            await ctx.message.reply("`🟢 Staff`", mention=False)
        else:
            await ctx.message.reply(
                ":x: You are unable to use this command.", mention=False
            )

    async def _edit_roles(
        self, server: revolt.Server, member: revolt.Member, roles
    ) -> None:
        """
        Monkey-patch of `ctx.author.edit` since it having
        400 (bad request) HTTP error when tring to edit something.
        """
        await self.bot.http.request(
            "PATCH",
            f"/servers/{server.id}/members/{member.id}",
            json={"remove": None, "roles": roles},
        )


def setup(bot: commands.CommandsClient):
    return CogOneShot(bot)
