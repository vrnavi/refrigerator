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
            f"**Watch Thread** for {target}: {trackerthread.mention}\nLast message sent `never`."
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

        userlog = get_userlog()
        if userlog[str(target.id)]["watch"]["state"]:
            trackerthread = await self.bot.fetch_channel(
                userlog[str(target.id)]["watch"]["thread"]
            )
            await trackerthread.edit(archived=True)
            trackerlog = await self.bot.fetch_channel(
                config.guild_configs[ctx.guild.id]["logs"]["tracker_channel"]
            )
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

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if (
            not message.content
            or not message.guild
            or message.guild.id not in config.guild_configs
        ):
            return
        userlog = get_userlog()
        try:
            if userlog[str(message.author.id)]["watch"]["state"]:
                trackerthread = await self.bot.fetch_channel(
                    userlog[str(message.author.id)]["watch"]["thread"]
                )
                trackermsg = await self.bot.get_channel(
                    config.guild_configs[message.guild.id]["logs"]["tracker_channel"]
                ).fetch_message(userlog[str(message.author.id)]["watch"]["message"])
                embed = discord.Embed(
                    color=message.author.color,
                    description=f"{message.content}",
                    timestamp=message.created_at,
                )
                embed.set_footer(
                    text="Dishwasher", icon_url=self.bot.user.display_avatar
                )
                embed.set_author(
                    name=f"💬 {message.author} said in #{message.channel.name}...",
                    icon_url=f"{message.author.display_avatar.url}",
                )
                await trackerthread.send(embed=embed)
                await trackermsg.edit(
                    content=f"**Watch Thread** for {message.author}: {trackerthread.mention}\nLast message sent <t:{message.created_at.timestamp()}:f>"
                )
        except TypeError:
            # Old Farts.
            return
        except KeyError:
            return


async def setup(bot):
    await bot.add_cog(ModWatch(bot))
