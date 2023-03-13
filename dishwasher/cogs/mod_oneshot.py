import config
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff


class ModOneShot(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command(aliases=["pingmods", "summonmods"])
    async def pingmod(self, ctx):
        """[U] Pings mods, only use when there's an emergency.

        Abuse of this command can lead to warnings!"""
        can_ping = any(r.id in config.pingmods_allow for r in ctx.author.roles)
        if can_ping:
            await ctx.send(
                f"<@&{config.staff_role_ids[0]}>, {ctx.author.mention} needs assistance."
            )
        else:
            await ctx.send(
                f"You need the Strange Journal role to be able to ping the entire Staff team. Please pick an online Staff, and ping them instead."
            )

    @commands.guild_only()
    @commands.command(aliases=["togglemod"])
    async def modtoggle(self, ctx):
        """[S] Toggles your Staff role.

        If you have Staff, it will replace it with Ex-Staff, and vice versa."""
        staff_role = ctx.guild.get_role(config.staff_role_ids[0])
        exstaff_role = ctx.guild.get_role(config.exstaff_role_ids[0])

        if staff_role in ctx.author.roles:
            await ctx.author.remove_roles(
                staff_role, reason="Staff self-unassigned Staff role"
            )
            await ctx.author.add_roles(
                exstaff_role, reason="Staff self-unassigned Staff role"
            )
            await ctx.message.reply(content=f"Staff status: 🔴", mention_author=False)
        elif exstaff_role in ctx.author.roles:
            await ctx.author.add_roles(
                staff_role, reason="Staff self-assigned Staff role"
            )
            await ctx.author.remove_roles(
                exstaff_role, reason="Staff self-assigned Staff role"
            )
            await ctx.message.reply(content=f"Staff status: 🟢", mention_author=False)
        else:
            await ctx.send(f"You are unable to use this command.")


async def setup(bot):
    await bot.add_cog(ModOneShot(bot))
