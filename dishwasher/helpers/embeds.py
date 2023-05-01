import config
import discord
import datetime

header_types = {
    "msg_delete": "🗑️ Message Delete",
    "mem_join": "📥 User Joined",
    "mem_remove": "📥 User Left",
    "mem_ban": "⛔ Ban",
    "mem_unban": "🎁 Unban",
    "mem_update": "ℹ️ Member Update",
    "mem_kick": "👢 Kick",
    "serv_update": "🏡 Server Update",
    "channel_create": "🏠 Channel Created",
    "channel_delete": "🏚️ Channel Deleted",
    "channel_update": "🏘️ Channel Update",
    "role_create": "🏷️ Role Created",
    "role_delete": "🔥 Role Deleted",
    "role_update": "🖋️ Role Update",
}


def split_content(content):
    return list([content[i : i + 1020] for i in range(0, len(content), 1020)])


def make_fragments(embed, split_content):
    for i, c in enumerate(split_content):
        embed.add_field(
            name=f"🧩 Fragment {i+1}",
            value=f">>> {c}",
            inline=False,
        )


def make_mod(embed, target, staff, reason):
    embed.set_author(
        name=target,
        icon_url=target.display_avatar.url,
    )
    embed.add_field(
        name=f"👤 User",
        value=f"**{target}**\n{target.mention} ({target.id})",
        inline=True,
    )
    embed.add_field(
        name=f"🛠️ Staff",
        value=f"**{staff}**\n{staff.mention} ({staff.id})",
        inline=True,
    )
    embed.add_field(name=f"📝 Reason", value=reason, inline=False)


def make_embed(bot, kind, **kwargs):
    embed = discord.Embed(title=header_types[kind], timestamp=datetime.datetime.now())
    embed.set_footer(text=bot.user.name, icon_url=bot.user.display_avatar)

    if kind == "msg_delete":
        message = kwargs.get("message", None)
        embed.color = discord.Color.dark_gray()
        embed.description = f"{message.author.mention} ({message.author.id}) in {message.channel.mention}"
        name = f"🧾 Sent on <t:{message.created_at.astimezone().strftime('%s')}:f>:"
        embed.set_author(
            name=message.author,
            icon_url=message.author.display_avatar.url,
        )
        if len(message.clean_content) > 1024:
            embed.add_field(
                name=name,
                value=f"**Message was too long to post!** Split into fragments below.",
                inline=False,
            )
            make_fragments(embed, split_content(message.clean_content))
        else:
            embed.add_field(
                name=name,
                value=f">>> {message.clean_content}",
                inline=False,
            )
        embed.add_field(
            name="🔗 Original URL",
            value=f"```{message.jump_url}```",
            inline=False,
        )
    elif kind == "mem_join":
        member = kwargs.get("member", None)
        inv_used = kwargs.get("invite", None)
        embed.color = discord.Color.lighter_gray()
        embed.description = f"{member.mention} ({member.id})"
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(
            name=member,
            icon_url=member.display_avatar.url,
        )
        embed.add_field(
            name="⏰ Account created:",
            value=f"<t:{member.created_at.astimezone().strftime('%s')}:f>\n<t:{member.created_at.astimezone().strftime('%s')}:R>",
            inline=True,
        )
        embed.add_field(name="📨 Invite used:", value=f"{invite_used}", inline=True)
    elif kind == "mem_remove":
        member = kwargs.get("member", None)
        embed.color = discord.Color.darker_gray()
        embed.description = f"{member.mention} ({member.id})"
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(
            name=member,
            icon_url=member.display_avatar.url,
        )
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
    elif kind == "mem_kick":
        target = kwargs.get("target", None)
        staff = kwargs.get("staff", None)
        reason = kwargs.get("reason", None)
        embed.color = discord.Colour.from_str("#FFFF00")
        embed.description = (
            f"{target.mention} was kicked by {staff.mention} [External Method]"
        )
        make_mod(embed, target, staff, reason)
    elif kind == "mem_ban":
        target = kwargs.get("target", None)
        staff = kwargs.get("staff", None)
        reason = kwargs.get("reason", None)
        embed.color = discord.Colour.from_str("#FF0000")
        embed.description = (
            f"{target.mention} was banned by {staff.mention} [External Method]"
        )
        make_mod(embed, target, staff, reason)
    elif kind == "mem_unban":
        target = kwargs.get("target", None)
        staff = kwargs.get("staff", None)
        reason = kwargs.get("reason", None)
        embed.color = discord.Colour.from_str("#00FF00")
        embed.description = (
            f"{target.mention} was unbanned by {staff.mention} [External Method]"
        )
        make_mod(embed, target, staff, reason)
    elif kind == "mem_update":
        member_before = kwargs.get("member_before", None)
        member_after = kwargs.get("member_after", None)
        name_changed = kwargs.get("name_changed", None)
        nick_changed = kwargs.get("nick_changed", None)
        role_changed = kwargs.get("role_changed", None)
        embed.color = member_after.color
        embed.description = f"{member_after.mention} ({member_after.id})"
        embed.set_author(
            name=member_after,
            icon_url=member_after.display_avatar.url,
        )
        if name_changed:
            embed.add_field(
                name=f"📝 Username Change",
                value=f"❌ {member_before}\n⬇️\n⭕ {member_after}",
                inline=False,
            )
        if nick_changed:
            if not member_before.nick:
                fname = "🏷 Nickname Added"
            elif not member_after.nick:
                fname = "🏷 Nickname Removed"
            else:
                fname = "🏷 Nickname Changed"
            embed.add_field(
                name=fname,
                value=f"❌ {member_before.nick}\n⬇️\n⭕ {member_after.nick}",
                inline=False,
            )
        if role_changed:
            rolelist = kwargs.get("rolelist", None)
            embed.add_field(name=f"🎨 Role Change", value=rolelist, inline=False)

    return embed
