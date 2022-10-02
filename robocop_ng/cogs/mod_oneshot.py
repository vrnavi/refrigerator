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
        """Pings mods, only use when there's an emergency."""
        can_ping = any(r.id in config.pingmods_allow for r in ctx.author.roles)
        if can_ping:
            await ctx.send(
                f"<@&{config.pingmods_role}>: {ctx.author.mention} needs assistance."
            )
        else:
            await ctx.send(
                f"{ctx.author.mention}: You need the Strange Journal role to be able to ping the entire Staff team. Please pick an online Staff, and ping them instead."
            )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["togglemod"])
    async def modtoggle(self, ctx):
        """Toggles your Staff role, staff only."""
        staff_role = ctx.guild.get_role(config.staff_role)
        exstaff_role = ctx.guild.get_role(config.exstaff_role)

        if staff_role in ctx.author.roles:
            await ctx.author.remove_roles(
                staff_role, reason="Staff self-unassigned Staff role"
            )
            await ctx.author.add_roles(
                exstaff_role, reason="Staff self-unassigned Staff role"
            )
            await ctx.send(f"{ctx.author.mention}: Removed your Staff role.")
        else:
            await ctx.author.add_roles(
                staff_role, reason="Staff self-assigned Staff role"
            )
            await ctx.author.remove_roles(
                exstaff_role, reason="Staff self-assigned Staff role"
            )
            await ctx.send(f"{ctx.author.mention}: Gave your Staff role back.")


async def setup(bot):
    await bot.add_cog(ModOneShot(bot))
