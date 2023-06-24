import discord
import datetime


def username_system(user):
    part1 = (
        "**" + user.global_name + f"** [{user}]" if user.global_name else f"**{user}**"
    )
    part2 = "\n" + user.mention
    part3 = " (" + user.id + ")"
    return part1 + part2 + part3


def split_content(content):
    return list([content[i : i + 1020] for i in range(0, len(content), 1020)])


def slice_embed(embed, content, name):
    embed.add_field(
        name=name,
        value="**Message was too long to post!** Split into fragments below.",
        inline=False,
    )
    for i, c in enumerate(split_content(content)):
        embed.add_field(
            name=f"🧩 Fragment {i+1}",
            value=f">>> {c}",
            inline=False,
        )


def author_embed(embed, obj, thumbnail=False):
    if type(obj).__name__ == "Guild":
        embed.set_author(
            name=obj.name,
            icon_url=obj.icon.url,
        )
        if thumbnail:
            embed.set_thumbnail(url=obj.display_avatar.url)

    elif type(obj).__name__ == "Member":
        embed.set_author(
            name=obj.global_name + f" [{obj}]" if obj.global_name else str(obj),
            icon_url=obj.display_avatar.url,
        )
        if thumbnail:
            embed.set_thumbnail(url=obj.display_avatar.url)


def mod_embed(embed, target, staff, reason=None):
    embed.set_author(
        name=target,
        icon_url=target.display_avatar.url,
    )
    embed.add_field(
        name=f"👤 User",
        value=username_system(target),
        inline=True,
    )
    embed.add_field(
        name=f"🛠️ Staff",
        value=username_system(target),
        inline=True,
    )
    if reason:
        embed.add_field(name=f"📝 Reason", value=reason, inline=False)


def createdat_embed(embed, member):
    embed.add_field(
        name="⏰ Account created:",
        value=f"<t:{member.created_at.astimezone().strftime('%s')}:f>\n<t:{member.created_at.astimezone().strftime('%s')}:R>",
        inline=True,
    )


def joinedat_embed(embed, member):
    embed.add_field(
        name="⏱️ Account joined:",
        value=f"<t:{member.joined_at.astimezone().strftime('%s')}:f>\n<t:{member.joined_at.astimezone().strftime('%s')}:R>",
        inline=True,
    )


def stock_embed(bot):
    embed = discord.Embed(timestamp=datetime.datetime.now())
    embed.set_footer(text=bot.user.name, icon_url=bot.user.display_avatar)
    return embed
