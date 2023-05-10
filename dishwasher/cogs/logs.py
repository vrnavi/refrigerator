import discord
from discord.ext.commands import Cog
import json
import re
import config
import datetime
import os
from helpers.checks import check_if_staff
from helpers.userlogs import userlog, get_userlog
from helpers.configs import get_log_config
from helpers.embeds import make_embed


class Logs2(Cog):
    """
    An advanced logging mechanism, which logs to threads. Logs many changes.
    """

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if not get_log_config(member.guild.id, "ulog_thread"):
            return
        ulog = await self.bot.fetch_channel(
            get_log_config(member.guild.id, "ulog_thread")
        )

        # Deal with unreadable names before anything.
        readable = 0
        for b in member.display_name:
            if b.isalnum():
                readable += 1
        if readable < 1:
            await member.edit(
                nick="Unreadable Name", reason="Automatic Unreadable Name"
            )
        # Deal with "hoist" names. ᲼
        # WIP

        escaped_name = self.bot.escape_message(member)

        # Attempt to correlate the user joining with an invite
        if not os.path.exists(f"{self.bot.server_data}/{member.guild.id}/invites.json"):
            if not os.path.exists(f"{self.bot.server_data}/{member.guild.id}"):
                os.makedirs(f"{self.bot.server_data}/{member.guild.id}")
            with open(
                f"{self.bot.server_data}/{member.guild.id}/invites.json", "w"
            ) as f:
                f.write("{}")
        with open(f"{self.bot.server_data}/{member.guild.id}/invites.json", "r") as f:
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
        with open(f"{self.bot.server_data}/{member.guild.id}/invites.json", "w") as f:
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
        embed = make_embed(self.bot, "mem_join", member=member, invite=invite_used)
        embeds.append(embed)

        warns = get_userlog(member.guild.id)
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
            or not get_log_config(after.guild.id, "ulog_thread")
        ):
            return
        ulog = await self.bot.fetch_channel(
            get_log_config(after.guild.id, "ulog_thread")
        )

        # Prepare embed msg
        embed = discord.Embed(
            color=discord.Color.light_gray(),
            title="📝 Message Edit",
            description=f"{after.author.mention} ({after.author.id}) in {after.channel.mention} [[Jump]({after.jump_url})]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=self.bot.escape_message(after.author),
            icon_url=after.author.display_avatar.url,
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
                    inline=False,
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
                    inline=False,
                )
                ctr += 1
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
            or not get_log_config(message.guild.id, "ulog_thread")
        ):
            return
        ulog = await self.bot.fetch_channel(
            get_log_config(message.guild.id, "ulog_thread")
        )

        embed = make_embed(self.bot, "msg_delete", message=message)
        await ulog.send(embed=embed)

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        ulog = get_log_config(member.guild.id, "ulog_thread")
        mlog = get_log_config(member.guild.id, "mlog_thread")
        if not ulog and not mlog:
            return

        escaped_name = self.bot.escape_message(member)
        cutoff_ts = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=5
        )

        alog = [
            entry
            async for entry in member.guild.audit_logs(
                limit=1, action=discord.AuditLogAction.ban
            )
        ]
        if alog and alog[0].created_at >= cutoff_ts and alog[0].target.id == member.id:
            return

        alog = [
            entry
            async for entry in member.guild.audit_logs(
                limit=1, action=discord.AuditLogAction.kick
            )
        ]
        if alog and alog[0].target.id == member.id:
            if not alog[0].created_at <= cutoff_ts:
                if alog[0].user.id != self.bot.user.id:
                    userlog(
                        member.guild.id,
                        member.id,
                        alog[0].user,
                        f"Kicked by external method.",
                        "kicks",
                    )
                    if not mlog:
                        return
                    mlog = await self.bot.fetch_channel(mlog)

                    embed = make_embed(
                        self.bot,
                        "mem_kick",
                        target=member,
                        staff=alog[0].user,
                        reason=alog[0].reason,
                    )

                    await mlog.send(embed=embed)
                return

        if not ulog:
            return
        ulog = await self.bot.fetch_channel(ulog)

        embed = make_embed(self.bot, "mem_remove", member=member)
        await ulog.send(embed=embed)

    @Cog.listener()
    async def on_member_ban(self, guild, member):
        await self.bot.wait_until_ready()

        alog = [
            entry
            async for entry in guild.audit_logs(
                limit=1, action=discord.AuditLogAction.ban
            )
        ]
        if alog[0].user.id == self.bot.user.id or alog[0].target.id != member.id:
            return

        userlog(
            member.guild.id,
            member.id,
            alog[0].user,
            f"Banned by external method.",
            "bans",
        )

        mlog = get_log_config(guild.id, "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = make_embed(
            self.bot,
            "mem_ban",
            target=member,
            staff=alog[0].user,
            reason=alog[0].reason,
        )

        await mlog.send(embed=embed)

    @Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.bot.wait_until_ready()
        mlog = get_log_config(guild.id, "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        alog = [
            entry
            async for entry in guild.audit_logs(
                limit=1, action=discord.AuditLogAction.unban
            )
        ]
        if alog[0].user.id == self.bot.user.id:
            return

        embed = make_embed(
            self.bot,
            "mem_unban",
            target=user,
            staff=alog[0].user,
            reason=alog[0].reason,
        )
        await mlog.send(embed=embed)

    @Cog.listener()
    async def on_member_update(self, member_before, member_after):
        await self.bot.wait_until_ready()
        ulog = get_log_config(member_after.guild.id, "ulog_thread")
        if not ulog:
            return
        ulog = await self.bot.fetch_channel(ulog)

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

        role_changed = False
        rolelist = None
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
                role_changed = True

        name_changed = False
        if member_before.name != member_after.name:
            name_changed = True
        nick_changed = False
        if member_before.nick != member_after.nick:
            nick_changed = True

        if name_changed or nick_changed or role_changed:
            embed = make_embed(
                self.bot,
                "mem_update",
                member_before=member_before,
                member_after=member_after,
                name_changed=name_changed,
                nick_changed=nick_changed,
                role_changed=role_changed,
                rolelist = rolelist,
            )
            await ulog.send(embed=embed)

    @Cog.listener()
    async def on_guild_update(self, guild_before, guild_after):
        await self.bot.wait_until_ready()
        slog = get_log_config(guild_after.id, "slog_thread")
        if not slog:
            return
        slog = await self.bot.fetch_channel(slog)

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
            name=guild_after.name,
            icon_url=guild_after.icon.url,
        )

        if guild_before.name != guild_after.name:
            updated = True
            embed.add_field(
                name=f"📝 Name Change",
                value=f"❌ {guild_before.name}\n⬇️\n⭕ {guild_after.name}",
                inline=False,
            )

        if guild_after.banner and guild_before.banner.url != guild_after.banner.url:
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
        slog = get_log_config(channel.guild.id, "slog_thread")
        if not slog:
            return
        slog = await self.bot.fetch_channel(slog)

        embed = discord.Embed(
            color=discord.Colour.from_str("#00FFFF"),
            title="🏠 Channel Created",
            description=f"`{str(channel.category)}/`#{channel.name} ({channel.id}) [{channel.mention}]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=channel.guild.name,
            icon_url=channel.guild.icon.url,
        )
        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.bot.wait_until_ready()
        slog = get_log_config(channel.guild.id, "slog_thread")
        if not slog:
            return
        slog = await self.bot.fetch_channel(slog)

        embed = discord.Embed(
            color=discord.Colour.from_str("#FF00FF"),
            title="🏚️ Channel Deleted",
            description=f"`{str(channel.category)}/`#{channel.name} ({channel.id})",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=channel.guild.name,
            icon_url=channel.guild.icon.url,
        )
        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_channel_update(self, channel_before, channel_after):
        await self.bot.wait_until_ready()
        slog = get_log_config(channel_after.guild.id, "slog_thread")
        if not slog:
            return
        slog = await self.bot.fetch_channel(slog)

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
            name=channel_after.guild.name,
            icon_url=channel_after.guild.icon.url,
        )

        if channel_before.name != channel_after.name:
            updated = True
            embed.add_field(
                name=f"📝 Name Change",
                value=f"❌ {channel_before.name}\n⬇️\n⭕ {channel_after.name}",
                inline=False,
            )

        try:
            if channel_after.topic and channel_before.topic != channel_after.topic:
                updated = True
                embed.add_field(
                    name=f"✍️ Topic Change",
                    value=f"❌ {channel_before.topic}\n⬇️\n⭕ {channel_after.topic}",
                    inline=False,
                )
        except:
            pass

        if updated:
            await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_create(self, role):
        await self.bot.wait_until_ready()
        slog = get_log_config(role.guild.id, "slog_thread")
        if not slog:
            return
        slog = await self.bot.fetch_channel(slog)

        embed = discord.Embed(
            color=role.color,
            title="🏷️ Role Created",
            description=f"{role.name} ({role.id}) [<@&{role.id}>]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=role.guild.name,
            icon_url=role.guild.icon.url,
        )
        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.bot.wait_until_ready()
        slog = get_log_config(role.guild.id, "slog_thread")
        if not slog:
            return
        slog = await self.bot.fetch_channel(slog)

        embed = discord.Embed(
            color=role.color,
            title="🔥 Role Deleted",
            description=f"{role} ({role.id}) [{role.mention}]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=role.guild.name,
            icon_url=role.guild.icon.url,
        )
        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_update(self, role_before, role_after):
        await self.bot.wait_until_ready()
        slog = get_log_config(role_after.guild.id, "slog_thread")
        if not slog:
            return
        slog = await self.bot.fetch_channel(slog)

        updated = False
        # initialize embed
        embed = discord.Embed(
            color=role_after.color,
            title="🖋️ Role Update",
            description=f"{role_after} ({role_after.id}) [{role_after.mention}]",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(
            name=role_after.guild.name,
            icon_url=role_after.guild.icon.url,
        )

        if role_before.name != role_after.name:
            updated = True
            embed.add_field(
                name=f"📝 Name Change",
                value=f"❌ {role_before}\n⬇️\n⭕ {role_after}",
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
