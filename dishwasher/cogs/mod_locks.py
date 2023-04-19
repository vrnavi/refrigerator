from discord.ext import commands
from discord.ext.commands import Cog
import config
import discord
from helpers.checks import check_if_staff


class ModLocks(Cog):
    def __init__(self, bot):
        self.bot = bot

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
        await self.set_sendmessage(
            channel,
            config.guild_configs[channel.guild.id]["staff"]["staff_role"],
            True,
            issuer,
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def lock(self, ctx, soft: bool = False, channel: discord.TextChannel = None):
        """[S] Prevents people from speaking in a channel.

        Defaults to current channel."""
        if not channel:
            channel = ctx.channel
        mlog = await self.bot.fetch_channel(
            config.guild_configs[ctx.guild.id]["logs"]["mlog_thread"]
        )

        if not channel.permissions_for(ctx.guild.default_role).send_messages:
            roles = config.guild_configs[ctx.guild.id]["misc"]["authorized_roles"]
        elif not channel.permissions_for(ctx.guild.default_role).read_messages:
            roles = []
            for r in channel.changed_roles:
                if r.id == config.guild_configs[ctx.guild.id]["staff"]["staff_role"]:
                    continue
                if r.id in config.guild_configs[ctx.guild.id]["misc"]["bot_roles"]:
                    continue
                if channel.overwrites_for(r).send_messages:
                    roles.append(r.id)
        else:
            roles = [ctx.guild.default_role]

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

        if not channel.permissions_for(ctx.guild.default_role).send_messages:
            roles = config.guild_configs[ctx.guild.id]["misc"]["authorized_roles"]
        elif not channel.permissions_for(ctx.guild.default_role).read_messages:
            roles = []
            for r in channel.changed_roles:
                if r.id == config.guild_configs[ctx.guild.id]["staff"]["staff_role"]:
                    continue
                if r.id in config.guild_configs[ctx.guild.id]["misc"]["bot_roles"]:
                    continue
                if channel.overwrites_for(r).send_messages:
                    roles.append(r.id)
        else:
            roles = [ctx.guild.default_role]

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
            return await ctx.reply(
                random_self_msg(ctx.author.name), mention_author=False
            )
        elif target == self.bot.user:
            return await ctx.reply(
                random_bot_msg(ctx.author.name), mention_author=False
            )
        elif self.bot.check_if_target_is_staff(target):
            return await ctx.reply(
                "I cannot lockout Staff members.", mention_author=False
            )

        await ctx.channel.set_permissions(target, send_messages=False)
        await ctx.reply(content=f"{target} has been locked out.", mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def unlockout(self, ctx, target: discord.Member):
        if target == ctx.author:
            return await ctx.reply(
                random_self_msg(ctx.author.name), mention_author=False
            )
        elif target == self.bot.user:
            return await ctx.reply(
                random_bot_msg(ctx.author.name), mention_author=False
            )
        elif self.bot.check_if_target_is_staff(target):
            return await ctx.reply(
                "I cannot unlockout Staff members.", mention_author=False
            )

        await ctx.channel.set_permissions(target, overwrite=None)
        await ctx.reply(
            content=f"{target} has been unlocked out.", mention_author=False
        )


async def setup(bot):
    await bot.add_cog(ModLocks(bot))
