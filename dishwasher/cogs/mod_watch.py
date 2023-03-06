import discord
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff
from helpers.userlogs import setwatch


class ModWatch(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def watch(self, ctx, target, *, note: str = ""):
        """[S] Puts a user under watch."""
        # target handler
        # In the case of IDs.
        try:
            target_id = int(target)
            target = await self.bot.fetch_user(target_id)
        # In the case of mentions.
        except ValueError:
            target = await self.bot.fetch_user(target[2:-1])

        setwatch(target.id, ctx.author, True, target.name)
        await ctx.send(f"User is now on watch.")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def unwatch(self, ctx, target, *, note: str = ""):
        """[S] Removes a user from watch."""
        # target handler
        # In the case of IDs.
        try:
            target_id = int(target)
            target = await self.bot.fetch_user(target_id)
        # In the case of mentions.
        except ValueError:
            target = await self.bot.fetch_user(target[2:-1])

        setwatch(target.id, ctx.author, False, target.name)
        await ctx.send(f"User is now not on watch.")

async def setup(bot):
    await bot.add_cog(ModWatch(bot))
