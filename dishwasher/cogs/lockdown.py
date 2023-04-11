from discord.ext import commands
from discord.ext.commands import Cog
import config
import discord
from helpers.checks import check_if_staff


class Lockdown(Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_if_target_is_staff(self, target):
        return any(r.id in config.staff_role_ids for r in target.roles)

    async def set_sendmessage(
        self, channel: discord.TextChannel, role, allow_send, issuer
    ):
        try:
            roleobj = channel.guild.get_role(role)
            overrides = channel.overwrites_for(roleobj)
            overrides.send_messages = allow_send
            await channel.set_permissions(
                roleobj, overwrite=overrides, reason=str(issuer)
            )
        except:
            pass

    async def unlock_for_staff(self, channel: discord.TextChannel, issuer):
        for role in config.staff_role_ids:
            await self.set_sendmessage(channel, role, True, issuer)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def lock(self, ctx, channel: discord.TextChannel = None, soft: bool = False):
        """[S] Prevents people from speaking in a channel.

        Defaults to current channel."""
        if not channel:
            channel = ctx.channel
        mlog = await self.bot.fetch_channel(
            config.guild_configs[ctx.guild.id]["logs"]["mlog_thread"]
        )

        roles = None
        for key, lockdown_conf in config.lockdown_configs.items():
            if channel.id in lockdown_conf["channels"]:
                roles = lockdown_conf["roles"]

        if roles is None:
            roles = config.lockdown_configs["default"]["roles"]

        for role in roles:
            await self.set_sendmessage(channel, role, False, ctx.author)

        await self.unlock_for_staff(channel, ctx.author)

        public_msg = "🔒 Channel locked down. "
        if not soft:
            public_msg += (
                "Only Staff may speak. "
                '**Do not** bring the topic to other channels or risk action taken. This includes "What happened?" messages.'
            )

        await ctx.send(public_msg)
        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(ctx.author)
        )
        msg = f"🔒 **Lockdown**: {ctx.channel.mention} by {safe_name}"
        await mlog.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """[S] Unlocks speaking in current channel."""
        if not channel:
            channel = ctx.channel
        mlog = await self.bot.fetch_channel(
            config.guild_configs[ctx.guild.id]["logs"]["mlog_thread"]
        )

        roles = None
        for key, lockdown_conf in config.lockdown_configs.items():
            if channel.id in lockdown_conf["channels"]:
                roles = lockdown_conf["roles"]

        if roles is None:
            roles = config.lockdown_configs["default"]["roles"]

        await self.unlock_for_staff(channel, ctx.author)

        for role in roles:
            await self.set_sendmessage(channel, role, True, ctx.author)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(ctx.author)
        )
        await ctx.send("🔓 Channel unlocked.")
        msg = f"🔓 **Unlock**: {ctx.channel.mention} by {safe_name}"
        await mlog.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def lockout(self, ctx, target: discord.Member):
        if target == ctx.author:
            return await ctx.send("Don't hurt yourself like that.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.name}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I cannot lockout Staff members.")

        await ctx.channel.set_permissions(target, send_messages=False)
        await ctx.reply(content=f"{target} has been locked out.")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def unlockout(self, ctx, target: discord.Member):
        if target == ctx.author:
            return await ctx.send("**...How?**")
        elif target == self.bot.user:
            return await ctx.send(f"Leave me alone, weirdo.")
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I cannot unlockout Staff members.")

        await ctx.channel.set_permissions(target, overwrite=None)
        await ctx.reply(content=f"{target} has been unlocked out.")


async def setup(bot):
    await bot.add_cog(Lockdown(bot))
