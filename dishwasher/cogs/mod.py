import discord
from discord.ext import commands
from discord.ext.commands import Cog
import config
import datetime
import asyncio
from helpers.checks import check_if_staff, check_if_bot_manager
from helpers.userlogs import userlog
from helpers.restrictions import add_restriction, remove_restriction
import io


class Mod(Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_if_target_is_staff(self, target):
        return any(r.id in config.staff_role_ids for r in target.roles)

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def setguildicon(self, ctx, url):
        """[O] Changes the guild icon."""
        img_bytes = await self.bot.aiogetbytes(url)
        await ctx.guild.edit(icon=img_bytes, reason=str(ctx.author))
        await ctx.send(f"Done!")

        log_channel = self.bot.get_channel(config.modlog_channel)
        log_msg = (
            f"✏️ **Guild Icon Update**: {ctx.author} changed the guild icon."
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )
        img_filename = url.split("/")[-1].split("#")[0]  # hacky
        img_file = discord.File(io.BytesIO(img_bytes), filename=img_filename)
        await log_channel.send(log_msg, file=img_file)

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["boot"])
    async def kick(self, ctx, target: discord.Member, *, reason: str = ""):
        """[S] Kicks a user."""
        if target == ctx.author:
            return await ctx.send("**No.**")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.name}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send(
                "I cannot kick Staff members."
            )

        userlog(target.id, ctx.author, reason, "kicks", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"**You were kicked** from `{ctx.guild.name}`."
        if reason:
            dm_message += f'\n*The given reason is:* "{reason}".'
        dm_message += (
            "\n\nYou are able to rejoin the server,"
            " but please be sure to behave when participating again."
        )

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents kick issues in cases where user blocked bot
            # or has DMs disabled
            pass

        await target.kick(reason=f"[ Kick by {ctx.author} ] {reason}")
            
        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Colour.from_str("#FFFF00"), title="👢 Kick", description=f"{target.mention} was kicked by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url}])", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{self.bot.escape_message(target)}", icon_url=f"{target.display_avatar.url}")
        embed.add_field(
            name=f"👤 User",
            value=f"**{safe_name}**\n{target.mention} ({target.id})",
            inline=True
        )
        embed.add_field(
            name=f"🛠️ Staff",
            value=f"**{str(ctx.author)}**\n{ctx.author.mention} ({ctx.author.id})",
            inline=True
        )
        if reason:
            embed.add_field(
                name=f"📝 Reason",
                value=f"{reason}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason was set!**\nPlease use `pws kick <user> [reason]` in the future.\Kick reasons are sent to the user.",
                inline=False
            )

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(embed=embed)
        await ctx.send(f"**{target.mention}** was KICKED.")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["yeet"])
    async def ban(self, ctx, target, *, reason: str = ""):
        """[S] Bans a user."""
        # target handler
        # In the case of IDs.
        try:
            target_id = int(target)
            target = await self.bot.fetch_user(target_id)
        # In the case of mentions.
        except ValueError:
            target = await self.bot.fetch_user(target[2:-1])
            
        if target == ctx.author:
            return await ctx.send("**No.**")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.name}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I cannot ban Staff members.")

        if reason:
            userlog(target.id, ctx.author, reason, "bans", target.name)
        else:
            userlog(target.id, ctx.author, f"No reason provided. ({ctx.message.jump_url})", "bans", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        if ctx.guild.get_member(target.id) is not None:
            dm_message = f"**You were banned** from `{ctx.guild.name}`."
            if reason:
                dm_message += f'\n*The given reason is:* "{reason}".'
            dm_message += "\n\nThis ban does not expire, but you may appeal it here:\nhttps://os.whistler.page/appeal"
            try:
                await target.send(dm_message)
            except discord.errors.Forbidden:
                # Prevents ban issues in cases where user blocked bot
                # or has DMs disabled
                pass

        await target.ban(
            reason=f"[ Ban by {ctx.author} ] {reason}", delete_message_days=0
        )

        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Colour.from_str("#FF0000"), title="⛔ Ban", description=f"{target.mention} was banned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url}])", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{self.bot.escape_message(target)}", icon_url=f"{target.display_avatar.url}")
        embed.add_field(
            name=f"👤 User",
            value=f"**{safe_name}**\n{target.mention} ({target.id})",
            inline=True
        )
        embed.add_field(
            name=f"🛠️ Staff",
            value=f"**{str(ctx.author)}**\n{ctx.author.mention} ({ctx.author.id})",
            inline=True
        )
        if reason:
            embed.add_field(
                name=f"📝 Reason",
                value=f"{reason}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason provided!**\nPlease use `pws ban <user> [reason]` in the future.\nBan reasons are sent to the user.",
                inline=False
            )

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(embed=embed)
        await ctx.send(f"**{target.mention}** is now BANNED.")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["bandel"])
    async def dban(
        self, ctx, day_count: int, target, *, reason: str = ""
    ):
        """[S] Bans a user, with n days of messages deleted."""
        # In the case of IDs.
        try:
            target_id = int(target)
            target = await self.bot.fetch_user(target_id)
        # In the case of mentions.
        except ValueError:
            target = await self.bot.fetch_user(target[2:-1])

        if target == ctx.author:
            return await ctx.send("**No.**")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.name}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I cannot ban Staff members.")

        if day_count < 0 or day_count > 7:
            return await ctx.send(
                "Message delete day count must be between 0 and 7 days."
            )

        if reason:
            userlog(target.id, ctx.author, reason, "bans", target.name)
        else:
            userlog(target.id, ctx.author, f"No reason provided. ({ctx.message.jump_url})", "bans", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        if ctx.guild.get_member(target.id) is not None:
            dm_message = f"**You were banned** from `{ctx.guild.name}`."
            if reason:
                dm_message += f'\n*The given reason is:* "{reason}".'
            dm_message += "\n\nThis ban does not expire, but you may appeal it here:\nhttps://os.whistler.page/appeal"
            try:
                await target.send(dm_message)
            except discord.errors.Forbidden:
                # Prevents ban issues in cases where user blocked bot
                # or has DMs disabled
                pass

        await target.ban(
            reason=f"[ Ban by {ctx.author} ] {reason}",
            delete_message_days=day_count,
        )

        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Colour.from_str("#FF0000"), title="⛔ Ban", description=f"{target.mention} was banned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url}])", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{self.bot.escape_message(target)}", icon_url=f"{target.display_avatar.url}")
        embed.add_field(
            name=f"👤 User",
            value=f"**{safe_name}**\n{target.mention} ({target.id})",
            inline=True
        )
        embed.add_field(
            name=f"🛠️ Staff",
            value=f"**{str(ctx.author)}**\n{ctx.author.mention} ({ctx.author.id})",
            inline=True
        )
        if reason:
            embed.add_field(
                name=f"📝 Reason",
                value=f"{reason}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason provided!**\nPlease use `pws dban <user> [reason]` in the future.\nBan reasons are sent to the user.",
                inline=False
            )

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(embed=embed)
        await ctx.send(
            f"**{target.mention}** is now BANNED.\n{day_count} days of messages were deleted."
        )

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def massban(self, ctx, *, targets: str):
        """[S] Bans users with their IDs, doesn't message them."""
        msg = await ctx.send(f"🚨 **MASSBAN IN PROGRESS...** 🚨")
        targets_int = [int(target) for target in targets.strip().split(" ")]
        for target in targets_int:
            target_user = await self.bot.fetch_user(target)
            target_member = ctx.guild.get_member(target)
            if target == ctx.author.id:
                await ctx.send(f"(re: {target}) You can't do mod actions on yourself.")
                continue
            elif target == self.bot.user:
                await ctx.send(
                    f"(re: {target}) I'm sorry {ctx.author.name}, I'm afraid I can't do that."
                )
                continue
            elif target_member and self.check_if_target_is_staff(target_member):
                await ctx.send(
                    f"(re: {target}) I cannot ban Staff members."
                )
                continue

            userlog(target, ctx.author, f"Part of a massban. [[Jump]({ctx.message.jump_url})", "bans", target_user.name)

            safe_name = await commands.clean_content(escape_markdown=True).convert(
                ctx, str(target)
            )

            await ctx.guild.ban(
                target_user,
                reason=f"[ Ban by {ctx.author} ] Massban.",
                delete_message_days=0,
            )
            
            # Prepare embed msg
            embed = discord.Embed(
                color=discord.Colour.from_str("#FF0000"), title="🚨 Massban", description=f"{target.mention} was banned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url}])", timestamp=datetime.datetime.now()
            )
            embed.set_footer(text="Dishwasher")
            embed.set_author(name=f"{self.bot.escape_message(target)}", icon_url=f"{target.display_avatar.url}")
            embed.add_field(
                name=f"👤 User",
                value=f"**{safe_name}**\n{target.mention} ({target.id})",
                inline=True
            )
            embed.add_field(
                name=f"🛠️ Staff",
                value=f"**{str(ctx.author)}**\n{ctx.author.mention} ({ctx.author.id})",
                inline=True
            )

            log_channel = self.bot.get_channel(config.modlog_channel)
            await log_channel.send(chan_message)
        await msg.edit(f"All {len(targets_int)} users are now BANNED.")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def unban(self, ctx, target, *, reason: str = ""):
        """[S] Unbans a user with their ID, doesn't message them."""
        # In the case of IDs.
        try:
            target_id = int(target)
            target_user = await self.bot.fetch_user(target_id)
        # In the case of mentions.
        except ValueError:
            target_user = await self.bot.fetch_user(target[2:-1])

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await ctx.guild.unban(target_user, reason=f"[ Unban by {ctx.author} ] {reason}")
            
        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Colour.from_str("#00FF00"), title="🎁 Unban", description=f"{target.mention} was unbanned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url}])", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{self.bot.escape_message(target)}", icon_url=f"{target.display_avatar.url}")
        embed.add_field(
            name=f"👤 User",
            value=f"**{safe_name}**\n{target.mention} ({target.id})",
            inline=True
        )
        embed.add_field(
            name=f"🛠️ Staff",
            value=f"**{str(ctx.author)}**\n{ctx.author.mention} ({ctx.author.id})",
            inline=True
        )
        if reason:
            embed.add_field(
                name=f"📝 Reason",
                value=f"{reason}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason provided!**\nPlease use `pws unban <user> [reason]` in the future.",
                inline=False
            )

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(embed=embed)
        await ctx.send(f"{safe_name} is now UNBANNED.")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["silentban"])
    async def sban(self, ctx, target, *, reason: str = ""):
        """[S] Bans a user silently. Does not message them."""
        # target handler
        # In the case of IDs.
        try:
            target_id = int(target)
            target = await self.bot.fetch_user(target_id)
        # In the case of mentions.
        except ValueError:
            target = await self.bot.fetch_user(target[2:-1])

        if target == ctx.author:
            return await ctx.send("**No.**")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.name}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I cannot ban Staff members.")

        if reason:
            userlog(target.id, ctx.author, reason, "bans", target.name)
        else:
            userlog(target.id, ctx.author, f"No reason provided. ({ctx.message.jump_url})", "bans", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await target.ban(
            reason=f"{ctx.author}, reason: {reason}", delete_message_days=0
        )

        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Colour.from_str("#FF0000"), title="⛔ Silent Ban", description=f"{target.mention} was banned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url}])", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{self.bot.escape_message(target)}", icon_url=f"{target.display_avatar.url}")
        embed.add_field(
            name=f"👤 User",
            value=f"**{safe_name}**\n{target.mention} ({target.id})",
            inline=True
        )
        embed.add_field(
            name=f"🛠️ Staff",
            value=f"**{str(ctx.author)}**\n{ctx.author.mention} ({ctx.author.id})",
            inline=True
        )
        if reason:
            embed.add_field(
                name=f"📝 Reason",
                value=f"{reason}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason provided!**\nPlease use `pws sban <user> [reason]` in the future.",
                inline=False
            )

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["clear", "clr"])
    async def purge(self, ctx, arg1 = None, arg2 = None, arg3 = None, arg4 = None):
        """[S] Clears a given number of messages."""
        log_channel = self.bot.get_channel(config.modlog_channel)

        limit = 50
        channel = ctx.channel
        deleted = 0
        purgetype = "messages"
        if not arg1:
            deleted = len(await ctx.channel.purge(limit=50))
        elif type(arg1) == int:
            deleted = len(await ctx.channel.purge(limit=arg1))
        if type(arg2) == int:
            limit = arg2
        if type(arg3) == discord.TextChannel:
            channel = arg3
        
        if arg1 == "bots":
            purgetype = "bot messages"
            def is_bot(m):
                return m.author.bot
            deleted = len(await channel.purge(limit=limit, check=is_bot))
        elif arg1 == "embeds":
            def has_embed(m):
                if m.embeds or m.attachments or m.stickers:
                    return True
                else:
                    return False
            deleted = len(await channel.purge(limit=limit, check=has_embed))
        elif arg1 == "reacts":
            purgetype = "reactions"
            if type(arg2) == discord.Member:
                if type(arg3) == int:
                    limit = arg3
                if type(arg4) == discord.TextChannel:
                    channel = arg4
                async for msg in channel.history(limit=limit):
                   for react in msg.reactions:
                       if await react.users().find(lambda u: u == user):
                           deleted += 1
                           async for u in react.users():
                               await msg.remove_reaction(react, u)
            elif arg2 == "pick":
                msg_text = (
                    f"React to the reactions you want "
                    f"to remove. React to this message when done."
                )
                msg = await ctx.channel.send(msg_text)
                tasks = []
                def check(event):
                    # we only care about the user who is clearing reactions
                    if event.user_id != ctx.author.id:
                        return False
                    # this is how the user finishes
                    if event.message_id == msg.id:
                        return True
                    else:
                        # remove a reaction
                        async def impl():
                            msg = (
                                await self.bot.get_guild(event.guild_id)
                                .get_channel(event.channel_id)
                                .get_message(event.message_id)
                            )
        
                            def check_emoji(r):
                                if event.emoji.is_custom_emoji() == r.custom_emoji:
                                    if event.emoji.is_custom_emoji():
                                        return event.emoji.id == r.emoji.id
                                    else:
                                        # gotta love consistent APIs
                                        return event.emoji.name == r.emoji
                                else:
                                    return False
        
                            for reaction in filter(check_emoji, msg.reactions):
                                async for u in reaction.users():
                                    await reaction.message.remove_reaction(reaction, u)
        
                        # schedule immediately
                        tasks.append(asyncio.create_task(impl()))
                        return False

                try:
                    await self.bot.wait_for("raw_reaction_add", timeout=120.0, check=check)
                except asyncio.TimeoutError:
                    await msg.edit(content=f"Operation timed out.")
                else:
                    await asyncio.gather(*tasks)
                    await msg.edit(content=f"Operation complete.")
                return
            else:
                async for msg in channel.history(limit=limit):
                    if msg.reactions:
                        deleted += 1
                        await msg.clear_reactions()
        
        embed = discord.Embed(
            color=discord.Color.lighter_gray(), title="🗑 Purged", description=f"{str(ctx.author)} purged {deleted} {purgetype} in {channel.mention}.", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{str(ctx.author)}", icon_url=f"{ctx.author.display_avatar.url}")
        
        await log_channel.send(embed=embed)
        await ctx.send(f"🚮 `{deleted}` {purgetype} purged.", delete_after=5)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["botclear", "clrb"])
    async def botpurge(self, ctx, limit: int = 50, channel: discord.TextChannel = None):
        """[S] Clears a given number of messages from bots."""
        log_channel = self.bot.get_channel(config.modlog_channel)
        if not channel:
            channel = ctx.channel

        def is_bot(m):
            return m.author.bot

        deleted = await channel.purge(limit=limit, check=is_bot)
        
        embed = discord.Embed(
            color=discord.Color.lighter_gray(), title="🗑 Purged", description=f"{str(ctx.author)} purged {len(deleted)} messages in {channel.mention}.", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{str(ctx.author)}", icon_url=f"{ctx.author.display_avatar.url}")
        
        await log_channel.send(embed=embed)
        await ctx.send(f"🚮 `{len(deleted)}` messages purged.", delete_after=5)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["embedclear", "clre"])
    async def embedpurge(self, ctx, limit: int = 50, channel: discord.TextChannel = None):
        """[S] Clears a given number of messages with embeds."""
        log_channel = self.bot.get_channel(config.modlog_channel)
        if not channel:
            channel = ctx.channel

        def has_embed(m):
            if m.embeds or m.attachments or m.stickers:
                return True
            else:
                return False

        deleted = await channel.purge(limit=limit, check=has_embed)
        
        embed = discord.Embed(
            color=discord.Color.lighter_gray(), title="🗑 Purged", description=f"{str(ctx.author)} purged {len(deleted)} messages in {channel.mention}.", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{str(ctx.author)}", icon_url=f"{ctx.author.display_avatar.url}")
        
        await log_channel.send(embed=embed)
        await ctx.send(f"🚮 `{len(deleted)}` messages purged.", delete_after=5)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def warn(self, ctx, target, *, reason: str = ""):
        """[S] Warns a user."""
        # target handler
        # In the case of IDs.
        try:
            target_id = int(target)
            target = await self.bot.fetch_user(target_id)
        # In the case of mentions.
        except ValueError:
            target = await self.bot.fetch_user(target[2:-1])

        if target == ctx.author:
            return await ctx.send("No.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.name}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send(
                "I cannot warn Staff members."
            )

        log_channel = self.bot.get_channel(config.modlog_channel)
        warn_count = userlog(target.id, ctx.author, reason, "warns", target.name)
        
        if reason:
            warn_count = userlog(target.id, ctx.author, reason, "warns", target.name)
        else:
            warn_count = userlog(target.id, ctx.author, f"No reason provided. ({ctx.message.jump_url})", "warns", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )
        
        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Colour.from_str("#FFFF00"), title="🗞️ Warn #{warn_count}", description=f"{target.mention} was warned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url}])", timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{self.bot.escape_message(target)}", icon_url=f"{target.display_avatar.url}")
        embed.add_field(
            name=f"👤 User",
            value=f"**{safe_name}**\n{target.mention} ({target.id})",
            inline=True
        )
        embed.add_field(
            name=f"🛠️ Staff",
            value=f"**{str(ctx.author)}**\n{ctx.author.mention} ({ctx.author.id})",
            inline=True
        )
        if reason:
            embed.add_field(
                name=f"📝 Reason",
                value=f"{reason}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason was set!**\nPlease use `pws warn <user> [reason]` in the future.\Warn reasons are sent to the user.",
                inline=False
            )

        if ctx.guild.get_member(target.id) is not None:
            msg = f"**You were warned** on `{ctx.guild.name}`."
            if reason:
                msg += "\nThe given reason is: " + reason
            msg += (
                f"\n\nPlease read the rules in {config.rules_url}. "
                f"This is warn #{warn_count}."
            )
            try:
                await target.send(msg)
            except discord.errors.Forbidden:
                # Prevents log issues in cases where user blocked bot
                # or has DMs disabled
                pass

        await ctx.send(
            f"{target.mention} has been warned. This user now has {warn_count} warning(s)."
        )
        await log_channel.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setnick", "nick"])
    async def nickname(self, ctx, target: discord.Member, *, nick: str = ""):
        """[S] Sets a user's nickname.

        Just send .nickname <user> to wipe the nickname."""

        try:
            if nick:
                await target.edit(nick=nick, reason=str(ctx.author))
            else:
                await target.edit(nick=None, reason=str(ctx.author))

            await ctx.send("Successfully set nickname.")
        except discord.errors.Forbidden:
            await ctx.send(
                "I don't have the permission to set that user's nickname.\n"
                "User's top role may be above mine, or I may lack Manage Nicknames permission."
            )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["echo"])
    async def say(self, ctx, *, the_text: str):
        """[S] Repeats a given text."""
        await ctx.send(the_text)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["send"])
    async def speak(self, ctx, channel: discord.TextChannel, *, the_text: str):
        """[S] Posts a given text in a given channel."""
        await channel.send(the_text)
        await ctx.message.reply("👍", mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def reply(self, ctx, channel: discord.TextChannel, message: int, *, the_text: str):
        """[S] Replies to a message with a given text in a given channel."""
        await self.bot.get_partial_messageable(f"{channel.id}").get_partial_message(f"{message}").reply(content=f"{the_text}", mention_author=False)
        await ctx.message.reply("👍", mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setplaying", "setgame"])
    async def playing(self, ctx, *, game: str = ""):
        """[S] Sets the bot's currently played game name.

        Just send pws playing to wipe the playing state."""
        if game:
            await self.bot.change_presence(activity=discord.Game(name=game))
        else:
            await self.bot.change_presence(activity=None)

        await ctx.send("Successfully set game.")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setbotnick", "botnick", "robotnick"])
    async def botnickname(self, ctx, *, nick: str = ""):
        """[S] Sets the bot's nickname.

        Just send pws botnickname to wipe the nickname."""

        if nick:
            await ctx.guild.me.edit(nick=nick, reason=str(ctx.author))
        else:
            await ctx.guild.me.edit(nick=None, reason=str(ctx.author))

        await ctx.send("Successfully set bot nickname.")


async def setup(bot):
    await bot.add_cog(Mod(bot))
