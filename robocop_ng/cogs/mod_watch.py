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
    async def watch(self, ctx, target: discord.Member, *, note: str = ""):
        """[S] Puts a user under watch."""
        setwatch(target.id, ctx.author, True, target.name)
        await ctx.send(f"{ctx.author.mention}: user is now on watch.")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def watchid(self, ctx, target: int, *, note: str = ""):
        """[S] Puts a user under watch by ID."""
        setwatch(target, ctx.author, True, target.name)
        await ctx.send(f"{target.mention}: user is now on watch.")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def unwatch(self, ctx, target: discord.Member, *, note: str = ""):
        """[S] Removes a user from watch."""
        setwatch(target.id, ctx.author, False, target.name)
        await ctx.send(f"{ctx.author.mention}: user is now not on watch.")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def unwatchid(self, ctx, target: int, *, note: str = ""):
        """[S] Removes a user from watch by ID."""
        setwatch(target, ctx.author, False, target.name)
        await ctx.send(f"{target.mention}: user is now not on watch.")


async def setup(bot):
    await bot.add_cog(ModWatch(bot))
