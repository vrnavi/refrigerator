import discord
import config
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff
from helpers.userlogs import setwatch, get_userlog


class ModWatch(Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_if_target_is_staff(self, target):
        return any(r.id in config.staff_role_ids for r in target.roles)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def watch(self, ctx, target: discord.User, *, note: str = ""):
        """[S] Puts a user under watch."""
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot watch Staff members.")
        if target == ctx.author:
            return await ctx.send("**No.**")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.name}, I'm afraid I can't do that."
            )

        trackerlog = await self.bot.fetch_channel(
            config.guild_configs[ctx.guild.id]["logs"]["tracker_channel"]
        )
        trackerthread = await trackerlog.create_thread(name=f"{target.name} Watchlog")
        trackermsg = await trackerlog.send(
            f"**Watch Thread** for {target}: {trackerthread.mention}"
        )
        setwatch(
            target.id, ctx.author, True, target.name, trackerthread.id, trackermsg.id
        )
        await ctx.send(
            f"**User is now on watch.**\nRelay thread available at {trackerthread.mention}."
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def unwatch(self, ctx, target: discord.User, *, note: str = ""):
        """[S] Removes a user from watch."""
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot unwatch Staff members.")
        if target == ctx.author:
            return await ctx.send("**No.**")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.name}, I'm afraid I can't do that."
            )

        trackerlog = await self.bot.fetch_channel(
            config.guild_configs[ctx.guild.id]["logs"]["tracker_channel"]
        )
        userlog = get_userlog()
        if userlog[str(target.id)]["watch"]["state"]:
            trackerthread = await self.bot.fetch_channel(
                userlog[str(target.id)]["watch"]["thread"]
            )
            await trackerthread.edit(archived=True)
            trackermsg = await trackerlog.fetch_message(
                userlog[str(target.id)]["watch"]["message"]
            )
            await trackermsg.delete()
            setwatch(target.id, ctx.author, False, target.name, None)
            await ctx.reply("User is now not on watch.", mention_author=False)
        else:
            return await ctx.reply(
                content="User isn't on watch...", mention_author=False
            )


async def setup(bot):
    await bot.add_cog(ModWatch(bot))
