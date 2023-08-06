import revolt
from revolt.ext import commands
import config
import datetime
import asyncio
import pytz
from helpers.checks import check_if_staff, check_only_server, check_if_bot_can_ban
from helpers.userlogs import userlog
from helpers.placeholders import random_self_msg, random_bot_msg
from helpers.sv_config import get_config
from helpers.messageutils import message_to_url, get_dm_channel, create_embed_with_fields
from helpers.colors import colors


class Mod(commands.Cog):
    def __init__(self, bot: commands.CommandsClient):
        self.bot = bot
        self.bot.modqueue = {}

    def check_if_target_is_staff(self, target: revolt.Member):
        return any(
            r.id == get_config(target.server.id, "staff", "staff_role")
            for r in target.roles
        )

    @commands.check(check_only_server)
    @commands.check(lambda ctx: ctx.server.get_member(ctx.state.me.id).has_permissions(kick_members=True))
    @commands.check(check_if_staff)
    @commands.command(aliases=["boot"])
    async def kick(self, ctx: commands.Context, target: commands.MemberConverter, *, reason: str = ""):
        """[S] Kicks a user."""
        if target == ctx.author:
            return await ctx.send(random_self_msg(ctx.author.name))
        elif target == self.bot.user:
            return await ctx.send(random_bot_msg(ctx.author.name))
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I cannot kick Staff members.")

        userlog(ctx.server.id, target.id, ctx.author, reason, "kicks")

        dm_message = f"**You were kicked** from `{ctx.server.name}`."
        if reason:
            dm_message += f'\n*The given reason is:* "{reason}".'
        dm_message += "\n\nYou are able to rejoin."

        try:
            channel = await get_dm_channel(self.bot, target)
            await channel.send(dm_message)
        except:
            pass

        await target.kick()
        await ctx.send(f"**{target.mention}** was KICKED.")

        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = revolt.SendableEmbed(
            colour="#FFFF00",
            title="👢 Kick",
            description=f"{target.mention} was kicked by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({message_to_url(ctx.message)})]",
        )

        embed = create_embed_with_fields(
            title="👢 Kick",
            color="#FFFF00",
            description=f"{target.mention} was kicked by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({message_to_url(ctx.message)})]",
            fields=[
                ("👤 User", f"**{target.original_name}#{target.discriminator}**\n{target.mention} ({target.id})"),
                ("🛠️ Staff", f"**{ctx.author.original_name}#{ctx.author.discriminator}**\n{ctx.author.mention} ({ctx.author.id})"),
                ("📝 Reason", f"{reason}" if reason else f"**No reason provided!**\nPlease use `{config.prefixes[0]}kick <user> [reason]` in the future.\nKick reasons are sent to the user."),
            ]
        )

        await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_bot_can_ban)
    @commands.check(check_if_staff)
    @commands.command(aliases=["yeet"])
    async def ban(self, ctx: commands.Context, target: commands.MemberConverter, *, reason: str = ""):
        """[S] Bans a user."""
        if target == ctx.author:
            return await ctx.send(random_self_msg(ctx.author.name))
        elif target == self.bot.user:
            return await ctx.send(random_bot_msg(ctx.author.name))
        if ctx.server.get_member(target.id):
            target = ctx.server.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if reason:
            userlog(ctx.server.id, target.id, ctx.author, reason, "bans")
        else:
            userlog(
                ctx.server.id,
                target.id,
                ctx.author,
                f"No reason provided. ({message_to_url(ctx.message)})",
                "bans",
            )

        if ctx.server.get_member(target.id) is not None:
            dm_message = f"**You were banned** from `{ctx.server.name}`."
            if reason:
                dm_message += f'\n*The given reason is:* "{reason}".'
            dm_message += "\n\nThis ban does not expire, but you may appeal it here:\nhttps://os.whistler.page/appeal"
            try:
                dm_channel = await get_dm_channel(self.bot, target)
                await dm_channel.send(dm_message)
            except:
                pass

        await target.ban(reason=f"{ctx.author.original_name}#{ctx.author.discriminator}, reason: {reason}")
        await ctx.send(f"**{target.mention}** is now BANNED.")

        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = create_embed_with_fields(
            title="⛔ Ban",
            color="#FF0000",
            description=f"{target.mention} was banned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({message_to_url(ctx.message)})]",
            fields=[
                ("👤 User", f"**{target.original_name}#{target.discriminator}**\n{target.mention} ({target.id})"),
                ("🛠️ Staff", f"**{ctx.author.original_name}#{ctx.author.discriminator}**\n{ctx.author.mention} ({ctx.author.id})"),
                ("📝 Reason", f"{reason}" if reason else f"**No reason provided!**\nPlease use `{config.prefixes[0]}ban <user> [reason]` in the future.\nBan reasons are sent to the user."),
            ]
        )

        await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_bot_can_ban)
    @commands.check(check_if_staff)
    @commands.command()
    async def massban(self, ctx: commands.Context, *, targets: str):
        """[S] Bans users with their IDs, doesn't message them."""
        msg = await ctx.send(f"🚨 **MASSBAN IN PROGRESS...** 🚨")
        targets_int = [int(target) for target in targets.strip().split(" ")]
        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if mlog:
            mlog = await self.bot.fetch_channel(mlog)
        for target in targets_int:
            target_user = await self.bot.fetch_user(target)
            target_member = ctx.server.get_member(target)
            if target == ctx.author.id:
                await ctx.send(random_self_msg(ctx.author.name))
                continue
            elif target == self.bot.user:
                await ctx.send(random_bot_msg(ctx.author.name))
                continue
            elif target_member and self.check_if_target_is_staff(target_member):
                await ctx.send(f"(re: {target}) I cannot ban Staff members.")
                continue

            userlog(
                ctx.server.id,
                target,
                ctx.author,
                f"Part of a massban. [[Jump]({message_to_url(ctx.message)})]",
                "bans",
            )

            await target_member.ban(reason=f"[ Ban by {ctx.author} ] Massban.")

            if not mlog:
                continue

            embed = create_embed_with_fields(
                title="🚨 Massban",
                color="#FF0000",
                description=f"{target_user.mention} was banned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({message_to_url(ctx.message)})]",
                fields=[
                    ("👤 User", f"**{target_user.name}**\n{target_user.mention} ({target_user.id})"),
                    ("🛠️ Staff", f"**{ctx.author.name}**\n{ctx.author.mention} ({ctx.author.id})")
                ]
            )

            await mlog.send(embed=embed)
        await msg.edit(f"All {len(targets_int)} users are now BANNED.")

    @commands.check(check_only_server)
    @commands.check(check_if_bot_can_ban)
    @commands.check(check_if_staff)
    @commands.command()
    async def unban(self, ctx: commands.Context, target: commands.UserConverter, *, reason: str = ""):
        """[S] Unbans a user with their ID, doesn't message them."""

        member = ctx.server.get_member(target.id)
        await self.bot.http.unban_member(ctx.server.id, target.id)

        await ctx.send(f"{member.original_name}#{member.discriminator} is now UNBANNED.")

        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = create_embed_with_fields(
            title="🎁 Unban",
            color="#00FF00",
            description=f"{member.mention} was unbanned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({message_to_url(ctx.message)})]",
            fields=[
                ("👤 User", f"**{member.original_name}#{member.discriminator}**\n{member.mention} ({member.id})"),
                ("🛠️ Staff", f"**{ctx.author.original_name}#{ctx.author.discriminator}**\n{ctx.author.mention} ({ctx.author.id})"),
                ("📝 Reason", f"{reason}" if reason else f"**No reason provided!**\nPlease use `{config.prefixes[0]}unban <user> [reason]` in the future."),
            ]
        )

        await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_bot_can_ban)
    @commands.check(check_if_staff)
    @commands.command(aliases=["silentban"])
    async def sban(self, ctx: commands.Context, target: commands.MemberConverter, *, reason: str = ""):
        """[S] Bans a user silently. Does not message them."""
        if target == ctx.author:
            return await ctx.send(random_self_msg(ctx.author.name))
        elif target == self.bot.user:
            return await ctx.send(random_bot_msg(ctx.author.name))
        if ctx.server.get_member(target.id):
            target = ctx.server.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if reason:
            userlog(ctx.server.id, target.id, ctx.author, reason, "bans")
        else:
            userlog(
                ctx.server.id,
                target.id,
                ctx.author,
                f"No reason provided. ({message_to_url(ctx.message)})",
                "bans",
            )

        await target.ban(reason=f"{ctx.author.original_name}#{ctx.author.discriminator}, reason: {reason}")
        await ctx.send(f"{target.mention} is now silently BANNED.")

        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = create_embed_with_fields(
            title="⛔ Silent Ban",
            color="#FF0000",
            description=f"{target.mention} was banned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({message_to_url(ctx.message)})]",
            fields=[
                ("👤 User", f"**{target.original_name}#{target.discriminator}**\n{target.mention} ({target.id})"),
                ("🛠️ Staff", f"**{ctx.author.original_name}#{ctx.author.discriminator}**\n{ctx.author.mention} ({ctx.author.id})"),
                ("📝 Reason", f"{reason}" if reason else f"**No reason provided!**\nPlease use `{config.prefixes[0]}sban <user> [reason]` in the future."),
            ]
        )

        await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.group(aliases=["clear"])
    async def purge(self, ctx: commands.Context, limit: commands.IntConverter = 50, channel: commands.ChannelConverter = None):
        """[S] Clears a given number of messages."""
        if not channel:
            channel = ctx.channel
        if limit > 100:
            return await ctx.message.reply(
                content=f"You can only purge a maximum of 100 messages.",
                mention=False,
            )

        messages = await channel.history(limit=limit)
        # manually filter out messages older than 7 days
        # since messages older than 7 days can't be purged
        messages = list(filter(lambda m: m.created_at > datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=7), messages))

        if (len(messages) == 0):
            return await ctx.send("No messages were able to be purged.\nThis might be because all the messages in this channel are older than 7 days.")

        await channel.delete_messages(messages)
        await ctx.send(f"🚮 `{limit}` messages purged.")

        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = revolt.SendableEmbed(
            title="🗑 Purged",
            colour=colors.lighter_grey,
            description=f"{ctx.author.original_name}#{ctx.author.discriminator} purged {limit} messages in {channel.mention}."
        )

        await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @purge.command()
    async def bots(self, ctx: commands.Context, limit: commands.IntConverter = 50, channel: commands.ChannelConverter = None):
        """[S] Clears a given number of bot messages."""
        if not channel:
            channel = ctx.channel

        if (limit > 200):
            return await ctx.message.reply(
                f"You can only purge a maximum of 200 messages."
            )

        history = await channel.history(limit=100)
        filtered_history = list(filter(lambda m: m.author.bot, history))

        if len(history) == 0:
            return await ctx.send("No messages were able to be purged.\nThis might be because all the bot messages in this channel are older than 7 days.")

        if (len(filtered_history) > limit):
            filtered_history = filtered_history[:limit]

        while len(filtered_history) < limit:
            it = 0

            if (it == 5):
                break

            extra_history = await channel.history(before=history[-1].id)
            filtered_extra_history = list(filter(lambda m: m.author.bot, extra_history))

            history += extra_history

            if (len(filtered_history) + len(filtered_extra_history) > limit):
                filtered_history += filtered_extra_history[:limit - len(filtered_history)]
            else:
                filtered_history += filtered_extra_history

            it += 1

        filtered_history = list(filter(lambda m: m.created_at > datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=7), filtered_history))

        if len(filtered_history) == 0:
            return await ctx.send("No messages were able to be purged.\nThis might be because all the bot messages in this channel are older than 7 days.")

        await channel.delete_messages(filtered_history)
        await ctx.send(f"🚮 `{len(filtered_history)}` bot messages purged.")

        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = revolt.SendableEmbed(
            title="🗑 Purged",
            colour=colors.lighter_grey,
            description=f"{ctx.author.original_name}#{ctx.author.discriminator} purged {len(filtered_history)} bot messages in {channel.mention}."
        )

        await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @purge.command(name="from")
    async def _from(
        self,
        ctx: commands.Context,
        target: commands.MemberConverter,
        limit: commands.IntConverter = 50,
        channel: commands.ChannelConverter = None,
    ):
        """[S] Clears a given number of messages from a user."""
        if (limit > 200):
            return await ctx.message.reply(
                f"You can only purge a maximum of 200 messages."
            )

        if not channel:
            channel = ctx.channel

        history = await channel.history(limit=100)
        filtered_history = list(filter(lambda m: m.author.id == target.id, history))

        if len(filtered_history) > limit:
            filtered_history = filtered_history[:limit]

        while len(filtered_history) < limit:
            it = 0

            if (it == 5):
                break

            extra_history = await channel.history(before=history[-1].id)
            filtered_extra_history = list(filter(lambda m: m.author.id == target.id, extra_history))

            if len(extra_history) == 0:
                break

            history += extra_history

            if (len(filtered_history) + len(filtered_extra_history) > limit):
                filtered_history += filtered_extra_history[:limit - len(history)]
            else:
                filtered_history += filtered_extra_history

            it += 1

        filtered_history = list(filter(lambda m: m.created_at > datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=7), filtered_history))

        if (len(filtered_history) == 0):
            return await ctx.send("No messages were able to be purged.\nThis might be because all the messages in this channel from the specified user are older than 7 days.")

        await ctx.channel.delete_messages(filtered_history)
        await ctx.send(f"🚮 `{len(filtered_history)}` messages from {target.original_name}#{target.discriminator} purged.")

        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = revolt.SendableEmbed(
            title="🗑 Purged",
            colour=colors.lighter_grey,
            description=f"{ctx.author.original_name}#{ctx.author.discriminator} purged {len(filtered_history)} messages from {target.original_name}#{target.discriminator} in {ctx.channel.mention}."
        )

        await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @purge.command(aliases=["emoji"])
    async def emotes(self, ctx: commands.Context, limit: commands.IntConverter = 50, channel: commands.ChannelConverter = None):
        """[S] Clears a given number of emotes."""
        if limit > 200:
            return await ctx.message.reply(
                f"You can only purge a maximum of 200 messages."
            )

        if not channel:
            channel = ctx.channel

        history = await channel.history(limit=100)
        filtered_history = list(filter(lambda m: m.content.startswith(":") and m.content.endswith(":"), history))

        if (len(filtered_history) > limit):
            filtered_history = filtered_history[:limit]

        while len(filtered_history) < limit:
            it = 0

            if (it == 5):
                break

            extra_history = await channel.history(before=history[-1].id)
            filtered_extra_history = list(filter(lambda m: m.content.startswith(":") and m.content.endswith(":"), extra_history))

            if len(extra_history):
                break

            history += extra_history

            if (len(filtered_history) + len(filtered_extra_history) > limit):
                filtered_history += filtered_extra_history[:limit - len(history)]
            else:
                filtered_history += filtered_extra_history

            it += 1

        filtered_history = list(filter(lambda m: m.created_at > datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=7), filtered_history))

        if (len(filtered_history) == 0):
            return await ctx.send("No messages were able to be purged.\nThis might be because all the messages with emotes in this channel are older than 7 days.")

        await channel.delete_messages(filtered_history)
        await ctx.send(f"🚮 `{len(filtered_history)}` emotes purged.")

        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed  = revolt.SendableEmbed(
            title="🗑 Purged",
            colour=colors.lighter_grey,
            description=f"{ctx.author.original_name}#{ctx.author.discriminator} purged {len(filtered_history)} emotes in {channel.mention}."
        )

        await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @purge.command()
    async def embeds(self, ctx: commands.Context, limit: commands.IntConverter = 50, channel: commands.ChannelConverter = None):
        """[S] Clears a given number of embeds."""
        if limit > 200:
            return await ctx.message.reply(
                "You can only purge a maximum of 200 messages."
            )
        if not channel:
            channel = ctx.channel

        history = await channel.history(limit=100)
        filtered_history = list(filter(lambda m: len(m.embeds) > 0 or len(m.attachments) > 0, history))

        if (len(filtered_history) > limit):
            filtered_history = filtered_history[:limit]

        while len(history) < limit:
            it = 0

            if (it == 5):
                break

            extra_history = await channel.history(before=history[-1].id)
            filtered_extra_history = list(filter(lambda m: len(m.embeds) > 0 or len(m.attachments) > 0, extra_history))

            if len(extra_history) == 0:
                break

            if (len(filtered_history) + len(filtered_extra_history) > limit):
                filtered_history += filtered_extra_history[:limit - len(history)]
            else:
                filtered_history += filtered_extra_history

            it += 1

        filtered_history = list(filter(lambda m: m.created_at > datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=7), filtered_history))

        if len(filtered_history) == 0:
            return await ctx.send("No messages were able to be purged.\nThis might be because all the messages with embeds in this channel are older than 7 days.")

        await channel.delete_messages(filtered_history)
        await ctx.send(f"🚮 `{len(filtered_history)}` embeds purged.")

        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = revolt.SendableEmbed(
            title="🗑 Purged",
            colour=colors.lighter_grey,
            description=f"{ctx.author.original_name}#{ctx.author.discriminator} purged {len(filtered_history)} embeds in {channel.mention}."
        )

        await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @purge.command()
    async def reacts(self, ctx: commands.Context, limit: commands.IntConverter = 50, channel: commands.ChannelConverter = None):
        """[S] Clears a given number of reactions."""
        if not channel:
            channel = ctx.channel

        deleted = 0
        history = await channel.history(limit=limit)

        for msg in history:
            if len(msg.reactions) > 0:
                deleted += 1
                await msg.remove_all_reactions()
                # If removed all at once, the bot hits the rate limit
                await asyncio.sleep(0.25)

        await ctx.send(f"🚮 `{deleted}` reactions purged.")

        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = revolt.SendableEmbed(
            title="🗑 Purged",
            colour=colors.lighter_grey,
            description=f"{ctx.author.original_name}#{ctx.author.discriminator} purged {deleted} reactions in {channel.mention}."
        )

        await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @purge.command()
    async def ireacts(self, ctx: commands.Context):
        """[S] Clears reactions interactively."""
        deleted = 0
        msg = await ctx.channel.send(
            content="🔎 **Interactive Reactions enabled.** React here when done."
        )
        tasks = []

        def check(message: revolt.Message, user: revolt.User, emoji: str):
            # we only care about the user who is clearing reactions
            if user.id != ctx.author.id:
                return False
            # this is how the user finishes
            if message.id == msg.id:
                return True
            else:
                # remove a reaction
                async def impl():
                    for reaction in filter(lambda e: e == emoji, message.reactions.keys()):
                        deleted += 1
                        await message.remove_reaction(reaction, remove_all=True)

                # schedule immediately
                tasks.append(asyncio.create_task(impl()))
                return False

        try:
            await self.bot.wait_for("reaction_add", timeout=120.0, check=check)
        except asyncio.TimeoutError:
            await msg.edit(content=f"Operation timed out.")
        else:
            await asyncio.gather(*tasks)
            await msg.edit(content=f"🚮 `{deleted}` reactions interactively purged.")

            mlog = get_config(ctx.server.id, "logs", "mlog_thread")
            if not mlog:
                return
            mlog = await self.bot.fetch_channel(mlog)

            embed = revolt.SendableEmbed(
                title="🗑 Purged",
                colour=colors.lighter_grey,
                description=f"{ctx.author.original_name}#{ctx.author.discriminator} purged {deleted} reactions interactively in {ctx.channel.mention}."
            )

            await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def warn(self, ctx: commands.Context, target: commands.MemberConverter, *, reason: str = ""):
        """[S] Warns a user."""
        if target.id == ctx.author.id:
            return await ctx.send(random_self_msg(ctx.author.name))
        elif target.id == self.bot.user.id:
            return await ctx.send(random_bot_msg(ctx.author.name))
        if ctx.server.get_member(target.id):
            target = ctx.server.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if reason:
            warn_count = userlog(ctx.server.id, target.id, ctx.author, reason, "warns")
        else:
            warn_count = userlog(
                ctx.server.id,
                target.id,
                ctx.author,
                f"No reason provided. ({message_to_url(ctx.message)})",
                "warns",
            )

        if ctx.server.get_member(target.id) is not None:
            msg = f"**You were warned** on `{ctx.server.name}`."
            if reason:
                msg += "\nThe given reason is: " + reason
            rulesmsg = (
                f" in {get_config(ctx.server.id, 'staff', 'rules_url')}."
                if get_config(ctx.server.id, "staff", "rules_url")
                else "."
            )
            msg += (
                f"\n\nPlease read the rules{rulesmsg} " f"This is warn #{warn_count}."
            )
            try:
                await target.send(msg)
            except:
                # Prevents warn issues in cases where user blocked bot
                # or has DMs disabled
                pass

        await ctx.send(
            f"{target.mention} has been warned. This user now has {warn_count} warning(s)."
        )

        mlog = get_config(ctx.server.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = create_embed_with_fields(
            title=f"Warn #{warn_count}",
            description=f"{target.mention} was warned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({message_to_url(ctx.message)})]",
            color="#FFFF00",
            fields=[
                ("👤 User", f"**{target.original_name}#{target.discriminator}**\n{target.mention} ({target.id})"),
                ("🛠️ Staff", f"**{ctx.author.original_name}#{ctx.author.discriminator}**\n{ctx.author.mention} ({ctx.author.id})"),
                ("📝 Reason", f"{reason}" if reason else f"**No reason provided!**\nPlease use `{config.prefixes[0]}warn <user> [reason]` in the future.\nWarn reasons are sent to the user."),
            ]
        )

        await mlog.send(embed=embed)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["setnick", "nick"])
    async def nickname(self, ctx: commands.Context, target: commands.MemberConverter, *, nick: str = ""):
        """[S] Sets a user's nickname.

        Just send .nickname <user> to wipe the nickname."""

        # this has to be done this way.
        # the "official" way (target.update(nick=nick)) just throws an error
        try:
            if nick:
                await self.bot.http.request("PATCH", f"/servers/{ctx.server.id}/members/{target.id}", json={"remove": None, "nickname": nick})
            else:
                await self.bot.http.request("PATCH", f"/servers/{ctx.server.id}/members/{target.id}", json={"remove": ["Nickname"]})

            await ctx.send("Successfully set nickname.")
        except revolt.errors.HTTPError as e:
            if (str(e) == "403"):
                await ctx.send(
                    "I don't have the permission to set that user's nickname.\n"
                    "User's top role may be above mine, or I may lack Manage Nicknames permission."
                )
            else:
                await ctx.send("I wasn't able to set that user's nickname that user due to an internal error.")

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["echo"])
    async def say(self, ctx: commands.Context, *, the_text: str):
        """[S] Repeats a given text."""
        await ctx.send(the_text)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["send"])
    async def speak(
        self,
        ctx: commands.Context,
        channel: commands.ChannelConverter,
        *,
        the_text: str,
    ):
        """[S] Posts a given text in a given channel."""
        await channel.send(the_text)
        await ctx.message.reply("👍")

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def reply(
        self,
        ctx: commands.Context,
        channel: commands.ChannelConverter,
        message: str,
        *,
        the_text: str,
    ):
        """[S] Replies to a message with a given text in a given channel."""
        msg = await channel.fetch_message(message)

        if message == None:
            return await ctx.send("Message not found.")

        await msg.reply(content=f"{the_text}")
        await ctx.message.reply("👍")

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def react(
        self,
        ctx: commands.Context,
        channel: commands.ChannelConverter,
        message: int,
        emoji: str,
    ):
        """[S] Reacts to a message with a given emoji in a given channel."""
        emoji = await self.bot.fetch_emoji(emoji)
        msg = await channel.fetch_message(message)
        await msg.add_reaction(emoji)
        await ctx.message.reply("👍")

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["setplaying", "setgame"])
    async def playing(self, ctx: commands.Context, *, game: str = ""):
        """[S] Sets the bot's currently played game name.

        Just send pws playing to wipe the playing state."""
        if game:
            await self.bot.edit_status(presence=revolt.PresenceType.online, text=game)
        else:
            await self.bot.edit_status(presence=revolt.PresenceType.online, text=None)

        await ctx.send("Successfully set game.")

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["setbotnick", "botnick", "robotnick"])
    async def botnickname(self, ctx: commands.Context, *, nick: str = ""):
        """[S] Sets the bot's nickname.

        Just send pws botnickname to wipe the nickname."""

        # It doesn't work unless you do it this way
        if nick:
            await self.bot.http.request("PATCH", f"/servers/{ctx.server.id}/members/{ctx.state.me.id}", json={"remove": None, "nickname": nick})
        else:
            await self.bot.http.request("PATCH", f"/servers/{ctx.server.id}/members/{ctx.state.me.id}", json={"remove": ["Nickname"]})

        await ctx.send("Successfully set bot nickname.")


def setup(bot: commands.CommandsClient):
    return Mod(bot)
