import discord
from discord.ext.commands import Cog
import json
import re
import config
import datetime
from helpers.checks import check_if_staff
from helpers.userlogs import userlog


class Logs2(Cog):
    """
    An advanced logging mechanism, which logs to threads. Logs many changes.
    """

    def __init__(self, bot):
        self.bot = bot
        self.invite_re = re.compile(
            r"((discord\.gg|discordapp\.com/" r"+invite)/+[a-zA-Z0-9-]+)", re.IGNORECASE
        )
        self.clean_re = re.compile(r"[^a-zA-Z0-9_ ]+", re.UNICODE)

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if member.guild.id not in config.guild_configs:
            return
        ulog = await self.bot.fetch_channel(
            config.guild_configs[member.guild.id]["logs"]["ulog_thread"]
        )

        # Deal with unreadable names before anything.
        readable = 0
        for b in member.display_name:
            if b.isalnum():
                readable = readable + 1
        if readable < 1:
            await member.edit(
                nick="Unreadable Name", reason="Automatic Unreadable Name"
            )
        # Deal with "hoist" names. ᲼
        # WIP

        escaped_name = self.bot.escape_message(member)

        # Attempt to correlate the user joining with an invite
        with open("data/invites.json", "r") as f:
            invites = json.load(f)

        real_invites = await member.guild.invites()

        # Add unknown active invites. Can happen if invite was manually created
        for invite in real_invites:
            if invite.id not in invites:
                invites[invite.id] = {
                    "uses": 0,
                    "url": invite.url,
                    "max_uses": invite.max_uses,
                    "code": invite.code,
                }

        probable_invites_used = []
        items_to_delete = []
        # Look for invites whose usage increased since last lookup
        for id, invite in invites.items():
            real_invite = next((x for x in real_invites if x.id == id), None)

            if real_invite is None:
                # Invite does not exist anymore. Was either revoked manually
                # or the final use was used up
                probable_invites_used.append(invite)
                items_to_delete.append(id)
            elif invite["uses"] < real_invite.uses:
                probable_invites_used.append(invite)
                invite["uses"] = real_invite.uses

        # Delete used up invites
        for id in items_to_delete:
            del invites[id]

        # Save invites data.
        with open("data/invites.json", "w") as f:
            f.write(json.dumps(invites))

        # Prepare the invite correlation message
        if len(probable_invites_used) == 1:
            invite_used = probable_invites_used[0]["code"]
        elif len(probable_invites_used) == 0:
            invite_used = "Unknown"
        else:
            invite_used = "One of: "
            invite_used += ", ".join([x["code"] for x in probable_invites_used])

        # Prepare embed message
        embeds = []
        embed = discord.Embed(
            color=discord.Color.lighter_gray(),
            title="📥 User Joined",
            description=f"<@{member.id}> ({member.id})",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{escaped_name}", icon_url=f"{member.display_avatar.url}"
        )
        embed.set_thumbnail(url=f"{member.display_avatar.url}")
        embed.add_field(
            name="⏰ Account created:",
            value=f"<t:{member.created_at.astimezone().strftime('%s')}:f>\n<t:{member.created_at.astimezone().strftime('%s')}:R>",
            inline=True,
        )
        embed.add_field(name="📨 Invite used:", value=f"{invite_used}", inline=True)
        embeds.append(embed)

        # Real hell zone.
        with open(f"data/userlogs/{member.guild.id}/userlog.json", "r") as f:
            warns = json.load(f)
        try:
            if len(warns[str(member.id)]["warns"]) != 0:
                embed = discord.Embed(
                    color=discord.Color.red(),
                    title="⚠️ This user has warnings!",
                    timestamp=datetime.datetime.now(),
                )
                embed.set_footer(
                    text=self.bot.user.name, icon_url=self.bot.user.display_avatar
                )
                for idx, warn in enumerate(warns[str(member.id)]["warns"]):
                    timestamp = datetime.datetime.strptime(
                        warn["timestamp"], "%Y-%m-%d %H:%M:%S"
                    ).strftime("%s")
                    embed.add_field(
                        name=f"Warn {idx + 1}: <t:{timestamp}:f> (<t:{timestamp}:R>)",
                        value=f"__Issuer:__ <@{warn['issuer_id']}> ({warn['issuer_id']})\n"
                        f"\n__Reason:__ {warn['reason']}",
                        inline=False,
                    )
                embeds.append(embed)
        except KeyError:  # if the user is not in the file
            pass

        await ulog.send(embeds=embeds)

    @Cog.listener()
    async def on_message_edit(self, before, after):
        await self.bot.wait_until_ready()
        if (
            after.author.bot
            or not after.guild
            or before.clean_content == after.clean_content
            or after.guild.id not in config.guild_configs
        ):
            return
        ulog = await self.bot.fetch_channel(
            config.guild_configs[after.guild.id]["logs"]["ulog_thread"]
        )

        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Color.light_gray(),
            title="📝 Message Edit",
            description=f"<@{after.author.id}> ({after.author.id}) [{after.channel.mention}] [[Jump]({after.jump_url})]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{self.bot.escape_message(after.author)}",
            icon_url=f"{after.author.display_avatar.url}",
        )
        # Split if too long.
        if len(before.clean_content) > 1024:
            split_before_msg = list(
                [
                    before.clean_content[i : i + 1020]
                    for i in range(0, len(before.clean_content), 1020)
                ]
            )
            embed.add_field(
                name=f"❌ Before on <t:{before.created_at.astimezone().strftime('%s')}:f>",
                value=f"**Message was too long to post!** Split into fragments below.",
                inline=False,
            )
            ctr = 1
            for p in split_before_msg:
                embed.add_field(
                    name=f"🧩 Fragment {ctr}",
                    value=f">>> {p}",
                    inline=True,
                )
                ctr += 1
        else:
            embed.add_field(
                name=f"❌ Before on <t:{before.created_at.astimezone().strftime('%s')}:f>",
                value=f">>> {before.clean_content}",
                inline=False,
            )
        if len(after.clean_content) > 1024:
            split_after_msg = list(
                [
                    after.clean_content[i : i + 1020]
                    for i in range(0, len(after.clean_content), 1020)
                ]
            )
            embed.add_field(
                name=f"⭕ After on <t:{after.edited_at.astimezone().strftime('%s')}:f>",
                value=f"**Message was too long to post!** Split into fragments below.",
                inline=False,
            )
            ctr = 1
            for p in split_after_msg:
                embed.add_field(
                    name=f"🧩 Fragment {ctr}",
                    value=f">>> {p}",
                    inline=True,
                )
                ctr = ctr + 1
        else:
            embed.add_field(
                name=f"⭕ After on <t:{after.edited_at.astimezone().strftime('%s')}:f>",
                value=f">>> {after.clean_content}",
                inline=False,
            )
        await ulog.send(embed=embed)

    @Cog.listener()
    async def on_message_delete(self, message):
        await self.bot.wait_until_ready()
        if (
            message.author.bot
            or not message.guild
            or message.guild.id not in config.guild_configs
        ):
            return
        ulog = await self.bot.fetch_channel(
            config.guild_configs[message.guild.id]["logs"]["ulog_thread"]
        )

        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Color.dark_gray(),
            title="🗑️ Message Delete",
            description=f"<@{message.author.id}> ({message.author.id}) [{message.channel.mention}]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{self.bot.escape_message(message.author)}",
            icon_url=f"{message.author.display_avatar.url}",
        )

        # Split if too long.
        if len(message.clean_content) > 1024:
            split_msg = list(
                [
                    message.clean_content[i : i + 1020]
                    for i in range(0, len(message.clean_content), 1020)
                ]
            )
            embed.add_field(
                name=f"🧾 Sent on <t:{message.created_at.astimezone().strftime('%s')}:f>:",
                value=f"**Message was too long to post!** Split into fragments below.",
                inline=False,
            )
            ctr = 1
            for p in split_msg:
                embed.add_field(
                    name=f"🧩 Fragment {ctr}",
                    value=f">>> {p}",
                    inline=True,
                )
                ctr = ctr + 1
        else:
            embed.add_field(
                name=f"🧾 Sent on <t:{message.created_at.astimezone().strftime('%s')}:f>:",
                value=f">>> {message.clean_content}",
                inline=True,
            )
        await ulog.send(embed=embed)

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        if member.guild.id not in config.guild_configs:
            return
        ulog = await self.bot.fetch_channel(
            config.guild_configs[member.guild.id]["logs"]["ulog_thread"]
        )
        mlog = await self.bot.fetch_channel(
            config.guild_configs[member.guild.id]["logs"]["mlog_thread"]
        )

        escaped_name = self.bot.escape_message(member)

        alog = [
            entry
            async for entry in member.guild.audit_logs(
                limit=1, action=discord.AuditLogAction.ban
            )
        ]
        if alog[0].target.id == member.id:
            return

        alog = [
            entry
            async for entry in member.guild.audit_logs(
                limit=1, action=discord.AuditLogAction.kick
            )
        ]
        if alog[0].target.id == member.id:
            if alog[0].user.id != self.bot.user.id:
                userlog(
                    member.id,
                    alog[0].user,
                    f"Kicked by external method.",
                    "kicks",
                    member.name,
                )
                embed = discord.Embed(
                    color=discord.Colour.from_str("#FFFF00"),
                    title="👢 Kick",
                    description=f"{alog[0].target.mention} was kicked by {alog[0].user.mention} [External Method]",
                    timestamp=datetime.datetime.now(),
                )
                embed.set_footer(
                    text=self.bot.user.name, icon_url=self.bot.user.display_avatar
                )
                embed.set_author(
                    name=f"{self.bot.escape_message(alog[0].target)}",
                    icon_url=f"{alog[0].target.display_avatar.url}",
                )
                embed.add_field(
                    name=f"👤 User",
                    value=f"**{escaped_name}**\n{alog[0].target.mention} ({alog[0].target.id})",
                    inline=True,
                )
                embed.add_field(
                    name=f"🛠️ Staff",
                    value=f"**{str(alog[0].user)}**\n{alog[0].user.mention} ({alog[0].user.id})",
                    inline=True,
                )
                embed.add_field(
                    name=f"📝 Reason", value=f"{str(alog[0].reason)}", inline=False
                )
                await mlog.send(embed=embed)
            return

        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Color.darker_gray(),
            title="📥 User Left",
            description=f"<@{member.id}> ({member.id})",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{escaped_name}", icon_url=f"{member.display_avatar.url}"
        )
        embed.set_thumbnail(url=f"{member.display_avatar.url}")
        embed.add_field(
            name="⏰ Account created:",
            value=f"<t:{member.created_at.astimezone().strftime('%s')}:f>\n<t:{member.created_at.astimezone().strftime('%s')}:R>",
            inline=True,
        )
        embed.add_field(
            name="⏱️ Account joined:",
            value=f"<t:{member.joined_at.astimezone().strftime('%s')}:f>\n<t:{member.joined_at.astimezone().strftime('%s')}:R>",
            inline=True,
        )

        await ulog.send(embed=embed)

    @Cog.listener()
    async def on_member_ban(self, guild, member):
        await self.bot.wait_until_ready()
        if guild.id not in config.guild_configs:
            return
        mlog = await self.bot.fetch_channel(
            config.guild_configs[guild.id]["logs"]["mlog_thread"]
        )

        alog = [
            entry
            async for entry in guild.audit_logs(
                limit=1, action=discord.AuditLogAction.ban
            )
        ]
        if alog[0].user.id == self.bot.user.id or alog[0].target.id != member.id:
            return

        userlog(
            member.id, alog[0].user, f"Banned by external method.", "bans", member.name
        )
        escaped_name = self.bot.escape_message(member)

        embed = discord.Embed(
            color=discord.Colour.from_str("#FF0000"),
            title="⛔ Ban",
            description=f"{alog[0].target.mention} was banned by {alog[0].user.mention} [External Method]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{self.bot.escape_message(alog[0].target)}",
            icon_url=f"{alog[0].target.display_avatar.url}",
        )
        embed.add_field(
            name=f"👤 User",
            value=f"**{escaped_name}**\n{alog[0].target.mention} ({alog[0].target.id})",
            inline=True,
        )
        embed.add_field(
            name=f"🛠️ Staff",
            value=f"**{str(alog[0].user)}**\n{alog[0].user.mention} ({alog[0].user.id})",
            inline=True,
        )
        embed.add_field(name=f"📝 Reason", value=f"{str(alog[0].reason)}", inline=False)
        await mlog.send(embed=embed)

    @Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.bot.wait_until_ready()
        if guild.id not in config.guild_configs:
            return
        mlog = await self.bot.fetch_channel(
            config.guild_configs[guild.id]["logs"]["mlog_thread"]
        )

        alog = [
            entry
            async for entry in guild.audit_logs(
                limit=1, action=discord.AuditLogAction.unban
            )
        ]
        if alog[0].user.id == self.bot.user.id:
            return
        escaped_name = self.bot.escape_message(user)
        embed = discord.Embed(
            color=discord.Colour.from_str("#00FF00"),
            title="🎁 Unban",
            description=f"{user.mention} was unbanned by {alog[0].user.mention} [External Method]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{self.bot.escape_message(user)}",
            icon_url=f"{user.display_avatar.url}",
        )
        embed.add_field(
            name=f"👤 User",
            value=f"**{escaped_name}**\n{user.mention} ({user.id})",
            inline=True,
        )
        embed.add_field(
            name=f"🛠️ Staff",
            value=f"**{str(alog[0].user)}**\n{alog[0].user.mention} ({alog[0].user.id})",
            inline=True,
        )
        embed.add_field(name=f"📝 Reason", value=f"{str(alog[0].reason)}", inline=False)
        await mlog.send(embed=embed)

    @Cog.listener()
    async def on_member_update(self, member_before, member_after):
        await self.bot.wait_until_ready()
        if member_after.guild.id not in config.guild_configs:
            return
        ulog = await self.bot.fetch_channel(
            config.guild_configs[member_after.guild.id]["logs"]["ulog_thread"]
        )

        # Swiftly deal with unreadable names.
        if member_before.display_name != member_after.display_name:
            readable = 0
            for b in member_after.display_name:
                if b.isalnum():
                    readable = readable + 1
            if readable < 1:
                await member_after.edit(
                    nick="Unreadable Name", reason="Automatic Unreadable Name"
                )
                return
        # Deal with "hoist" names. ᲼
        # WIP

        updated = False
        # initialize embed
        embed = discord.Embed(
            color=member_after.color,
            title="ℹ️ Member Update",
            description=f"{member_after.mention} ({self.bot.escape_message(member_after.id)})",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{self.bot.escape_message(member_after)}",
            icon_url=f"{member_after.display_avatar.url}",
        )

        if member_before.roles != member_after.roles:
            # role removal code
            role_removal = []
            for index, role in enumerate(member_before.roles):
                if role not in member_after.roles:
                    role_removal.append(role)
            # role addition code
            role_addition = []
            for index, role in enumerate(member_after.roles):
                if role not in member_before.roles:
                    role_addition.append(role)

            if len(role_addition) != 0 or len(role_removal) != 0:
                updated = True
                roles = []
                for role in role_removal:
                    roles.append("_~~" + role.name + "~~_")
                for role in role_addition:
                    roles.append("__**" + role.name + "**__")
                for index, role in enumerate(member_after.roles):
                    if role.name == "@everyone":
                        continue
                    if role not in role_removal and role not in role_addition:
                        roles.append(role.name)
                rolelist = "\n".join(reversed(roles))
                embed.add_field(
                    name=f"🎨 Role Change", value=f"{rolelist}", inline=False
                )

        if member_before.name != member_after.name:
            updated = True
            embed.add_field(
                name=f"📝 Username Change",
                value=f"❌ {self.bot.escape_message(member_before)}\n⬇️\n⭕ {self.bot.escape_message(member_after)}",
                inline=False,
            )
        if member_before.nick != member_after.nick:
            updated = True
            if not member_before.nick:
                fname = "🏷 Nickname Added"
            elif not member_after.nick:
                fname = "🏷 Nickname Removed"
            else:
                fname = "🏷 Nickname Changed"
            embed.add_field(
                name=f"{fname}",
                value=f"❌ {self.bot.escape_message(member_before.nick)}\n⬇️\n⭕ {self.bot.escape_message(member_after.nick)}",
                inline=False,
            )
        if updated:
            await ulog.send(embed=embed)

    @Cog.listener()
    async def on_guild_update(self, guild_before, guild_after):
        await self.bot.wait_until_ready()
        if guild_after.id not in config.guild_configs:
            return
        slog = await self.bot.fetch_channel(
            config.guild_configs[guild_after.id]["logs"]["slog_thread"]
        )

        updated = False
        # initialize embed
        embed = discord.Embed(
            color=discord.Colour.from_str("#FFCC00"),
            title="🏡 Server Update",
            description=f"{guild_after.name} with `{guild_after.member_count}` members.",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{guild_after.name}",
            icon_url=f"{guild_after.icon.url}",
        )

        if guild_before.name != guild_after.name:
            updated = True
            embed.add_field(
                name=f"📝 Name Change",
                value=f"❌ {guild_before.name}\n⬇️\n⭕ {guild_after.name}",
                inline=False,
            )

        if guild_before.banner.url != guild_after.banner.url:
            updated = True
            embed.add_field(
                name=f"🎨 Banner Change",
                value=f"If there is a new banner, it is below.",
                inline=False,
            )
            if guild_after.banner:
                embed.set_image(url=guild_after.banner.url)

        if updated:
            await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.bot.wait_until_ready()
        if channel.guild.id not in config.guild_configs:
            return
        slog = await self.bot.fetch_channel(
            config.guild_configs[channel.guild.id]["logs"]["slog_thread"]
        )

        embed = discord.Embed(
            color=discord.Colour.from_str("#00FFFF"),
            title="🏠 Channel Created",
            description=f"`{str(channel.category)}/`#{channel.name} ({channel.id}) [{channel.mention}]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{channel.guild.name}",
            icon_url=f"{channel.guild.icon.url}",
        )
        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.bot.wait_until_ready()
        if channel.guild.id not in config.guild_configs:
            return
        slog = await self.bot.fetch_channel(
            config.guild_configs[channel.guild.id]["logs"]["slog_thread"]
        )

        embed = discord.Embed(
            color=discord.Colour.from_str("#FF00FF"),
            title="🏚️ Channel Deleted",
            description=f"`{str(channel.category)}/`#{channel.name} ({channel.id})",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{channel.guild.name}",
            icon_url=f"{channel.guild.icon.url}",
        )
        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_channel_update(self, channel_before, channel_after):
        await self.bot.wait_until_ready()
        if channel_after.guild.id not in config.guild_configs:
            return
        slog = await self.bot.fetch_channel(
            config.guild_configs[channel_after.guild.id]["logs"]["slog_thread"]
        )

        updated = False
        # initialize embed
        embed = discord.Embed(
            color=discord.Colour.from_str("#FFFF00"),
            title="🏘️ Channel Update",
            description=f"{channel_after.name} ({channel_after.id}) [{channel_after.mention}]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{channel_after.guild.name}",
            icon_url=f"{channel_after.guild.icon.url}",
        )

        if channel_before.name != channel_after.name:
            updated = True
            embed.add_field(
                name=f"📝 Name Change",
                value=f"❌ {channel_before.name}\n⬇️\n⭕ {channel_after.name}",
                inline=False,
            )

        if updated:
            await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_create(self, role):
        await self.bot.wait_until_ready()
        if role.guild.id not in config.guild_configs:
            return
        slog = await self.bot.fetch_channel(
            config.guild_configs[role.guild.id]["logs"]["slog_thread"]
        )

        embed = discord.Embed(
            color=role.color,
            title="🏷️ Role Created",
            description=f"{role.name} ({role.id}) [<@&{role.id}>]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{role.guild.name}",
            icon_url=f"{role.guild.icon.url}",
        )
        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.bot.wait_until_ready()
        if role.guild.id not in config.guild_configs:
            return
        slog = await self.bot.fetch_channel(
            config.guild_configs[role.guild.id]["logs"]["slog_thread"]
        )

        embed = discord.Embed(
            color=role.color,
            title="🔥 Role Deleted",
            description=f"{role.name} ({role.id}) [<@&{role.id}>]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{role.guild.name}",
            icon_url=f"{role.guild.icon.url}",
        )
        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_update(self, role_before, role_after):
        await self.bot.wait_until_ready()
        if role_after.guild.id not in config.guild_configs:
            return
        slog = await self.bot.fetch_channel(
            config.guild_configs[role_after.guild.id]["logs"]["slog_thread"]
        )

        updated = False
        # initialize embed
        embed = discord.Embed(
            color=role_after.color,
            title="🖋️ Role Update",
            description=f"{role_after.name} ({role_after.id}) [<@&{role_after.id}>]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=f"{role_after.guild.name}",
            icon_url=f"{role_after.guild.icon.url}",
        )

        if role_before.name != role_after.name:
            updated = True
            embed.add_field(
                name=f"📝 Name Change",
                value=f"❌ {role_before.name}\n⬇️\n⭕ {role_after.name}",
                inline=False,
            )

        if role_before.color != role_after.color:
            updated = True
            embed.add_field(
                name=f"🌈 Color Change",
                value=f"❌ {str(role_before.color)}\n⬇️\n⭕ {str(role_after.color)}",
                inline=False,
            )

        if role_before.icon != role_after.icon:
            updated = True
            embed.add_field(
                name=f"ℹ️ Icon Change",
                value=f"If there is a new icon, it is to the right.",
                inline=False,
            )
            embed.set_thumbnail(role_after.icon.url)

        if role_before.hoist != role_after.hoist:
            updated = True
            embed.add_field(
                name=f"🆙 Hoist Change",
                value=f"❌ {str(role_before.hoist)}\n⬇️\n⭕ {str(role_after.hoist)}",
                inline=False,
            )

        if role_before.mentionable != role_after.mentionable:
            updated = True
            embed.add_field(
                name=f"1️⃣ Mentionable Change",
                value=f"❌ {str(role_before.mentionable)}\n⬇️\n⭕ {str(role_after.mentionable)}",
                inline=False,
            )

        if updated:
            await slog.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logs2(bot))
