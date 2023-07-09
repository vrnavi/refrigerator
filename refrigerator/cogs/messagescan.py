import re
import config
import datetime
import asyncio
import deepl
import revolt
from revolt.ext import commands
from helpers.checks import check_if_staff, check_only_server
from helpers.sv_config import get_config
from helpers.messageutils import message_to_url


class Messagescan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.on_message_listeners.append(on_message)
        self.bot.on_reaction_add_listeners.append(on_reaction_add)

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def snipe(self, ctx: commands.Context):
        if ctx.channel.id in self.bot.sniped:
            lastmsg: revolt.Message = self.bot.sniped[ctx.channel.id]
            # Prepare embed msg
            embed = revolt.SendableEmbed(
                description=lastmsg.content,
                icon_url=lastmsg.author.avatar.url if lastmsg.author.avatar else None,
                title=f"{lastmsg.author.original_name}#{lastmsg.author.discriminator}",
            )
            await ctx.message.reply(
                content=f"💬 {lastmsg.author.name} said in #{lastmsg.channel.name} on <t:{int(lastmsg.created_at.timestamp())}:f>...",
                embed=embed,
                mention=False,
            )
        else:
            await ctx.message.reply(
                content="There is no message delete in the snipe cache for this channel.",
                mention=False,
            )

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def snip(self, ctx: commands.Context):
        if ctx.channel.id in self.bot.snipped:
            lastbeforemsg: revolt.Message = self.bot.snipped[ctx.channel.id][0]
            lastaftermsg: revolt.Message = self.bot.snipped[ctx.channel.id][1]

            # Prepare embed msg
            embed = revolt.SendableEmbed(
                title=f"💬 {lastaftermsg.author.name}#{lastaftermsg.author.discriminator} said in #{lastaftermsg.channel.name}...",
                icon_url=lastaftermsg.author.avatar.url
                if lastaftermsg.author.avatar
                else None,
                description=f"❌ **Before on <t:{int(lastbeforemsg.created_at.timestamp())}:f>:**\n",
                url=message_to_url(lastaftermsg),
            )

            # Maximum of 2000 chars in an embed
            # so shove ellipsis on the end of it if it's too long
            if len(lastbeforemsg.content) > 900:
                embed.description += f"{lastbeforemsg.content[:900]}...\n\n"
            else:
                embed.description += f"{lastbeforemsg.content}\n\n"

            embed.description += (
                f"⭕ **After on <t:{int(lastaftermsg.created_at.timestamp())}:f>:**\n"
            )

            if len(lastaftermsg.content) > 900:
                embed.description += f"{lastaftermsg.content[:900]}..."
            else:
                embed.description += f"{lastaftermsg.content}"
            await ctx.message.reply(embed=embed, mention=False)
        else:
            await ctx.message.reply(
                content="There is no message edit in the snip cache for this channel.",
                mention=False,
            )

    async def usage(self, ctx: commands.Context):
        translation = deepl.Translator(config.deepl_key, send_platform_info=False)
        usage = translation.get_usage()

        await ctx.send(
            content=f"**DeepL limit counter:**\n**Characters:** `{usage.character.count}/{usage.character.limit}`\n**Documents:** `{usage.document.count}/{usage.document.limit}`"
        )


async def on_message(bot, message: revolt.Message):
    if (
        not message.content
        or message.author.bot
        or isinstance(message.channel, revolt.DMChannel)
        or not message.author.has_channel_permissions(message.channel, send_embeds=True)
        or not get_config(message.server.id, "misc", "embed_enable")
    ):
        pass

    msglinks: list[str] = re.compile(
        r"https://app\.revolt\.chat/server/[A-z0-9]{26}/channel/[A-z0-9]{26}/[A-z0-9]{26}",
        re.IGNORECASE,
    ).findall(message.content)

    twitterlinks: list[str] = re.compile(
        r"https://twitter\.com/[A-z0-9]+/status/[0-9]+", re.IGNORECASE
    ).findall(message.content)

    if not msglinks and not twitterlinks:
        return

    for link in msglinks + twitterlinks:
        parts = message.content.split(link)
        if parts[0].count("||") % 2 and parts[1].count("||") % 2:
            # Assume message is spoilered.
            try:
                msglinks.remove(link)
            except:
                twitterlinks.remove(link)

    tlinks = None
    embeds = None
    failed = False

    if twitterlinks:
        tlinks = "\n".join([t[:8] + "vx" + t[8:] for t in twitterlinks])

    if msglinks:
        embeds = []
        for m in msglinks:
            components = m.split("/")
            guildid = components[4]
            channelid = components[6]
            msgid = components[7]

            try:
                rcvguild = bot.get_server(guildid)
                rcvchannel: revolt.TextChannel = rcvguild.get_channel(channelid)
                rcvmessage = await rcvchannel.fetch_message(msgid)
            except:
                failed = True
                break

            # Prepare embed msg
            embed = revolt.SendableEmbed(
                title=f"💬 {rcvmessage.author.name} said in #{rcvmessage.channel.name}...",
                description=rcvmessage.content,
            )

            attachmentCount = len(rcvmessage.attachments)
            if attachmentCount > 0:
                if not rcvmessage.content:
                    embed.description = (
                        f"[View attachments]({message_to_url(rcvmessage)})"
                    )
                elif len(rcvmessage.content) > 1900:
                    embed.description = f"{rcvmessage.content[:1900]}...\n\n[View attachments]({message_to_url(rcvmessage)})"
                else:
                    embed.description = f"{rcvmessage.content}\n\n[View attachments]({message_to_url(rcvmessage)})"

            embeds.append(embed)

    if failed:
        await message.reply(
            content="Unable to quote a link you posted.\nI am either not in that guild, or I don't have permissions to view it.",
            mention_author=False,
        )

    def deletecheck(m):
        return m.id == message.id

    if tlinks or embeds:
        reply = await message.reply(content=tlinks, embeds=embeds, mention=False)
        try:
            await message.channel.fetch_message(message.id)
        except:
            await reply.delete()
        try:
            await bot.wait_for("message_delete", timeout=600, check=deletecheck)
            await reply.delete()
        except:
            pass


async def on_reaction_add(
    bot, message: revolt.Message, user: revolt.User, emoji_id: str
):
    langs = {
        "🇧🇬": {"name": "Bulgarian", "code": "BG"},
        "🇨🇿": {"name": "Czech", "code": "CS"},
        "🇩🇰": {"name": "Danish", "code": "DA"},
        "🇩🇪": {"name": "German", "code": "DE"},
        "🇬🇷": {"name": "Greek", "code": "EL"},
        "🇬🇧": {"name": "British English", "code": "EN-GB"},
        "🇺🇸": {"name": "American English", "code": "EN-US"},
        "🇪🇸": {"name": "Spanish", "code": "ES"},
        "🇪🇪": {"name": "Estonian", "code": "ET"},
        "🇫🇮": {"name": "Finnish", "code": "FI"},
        "🇫🇷": {"name": "French", "code": "FR"},
        "🇭🇺": {"name": "Hungarian", "code": "HU"},
        "🇮🇩": {"name": "Indonesian", "code": "ID"},
        "🇮🇹": {"name": "Italian", "code": "IT"},
        "🇯🇵": {"name": "Japanese", "code": "JA"},
        "🇰🇷": {"name": "Korean", "code": "KO"},
        "🇱🇹": {"name": "Lithuanian", "code": "LT"},
        "🇱🇻": {"name": "Latvian", "code": "LV"},
        "🇳🇴": {"name": "Norwegian", "code": "NB"},
        "🇳🇱": {"name": "Dutch", "code": "NL"},
        "🇵🇱": {"name": "Polish", "code": "PL"},
        "🇧🇷": {"name": "Brazilian Portugese", "code": "PT-BR"},
        "🇵🇹": {"name": "Portugese", "code": "PT-PT"},
        "🇷🇴": {"name": "Romanian", "code": "RO"},
        "🇷🇺": {"name": "Russian", "code": "RU"},
        "🇸🇰": {"name": "Slovak", "code": "SK"},
        "🇸🇮": {"name": "Slovenian", "code": "SL"},
        "🇸🇪": {"name": "Swedish", "code": "SV"},
        "🇹🇷": {"name": "Turkish", "code": "TR"},
        "🇺🇦": {"name": "Ukrainian", "code": "UK"},
        "🇨🇳": {"name": "Simplified Chinese", "code": "ZH"},
    }

    if (
        user.bot
        or emoji_id not in langs
        or len(message.reactions[emoji_id]) != 1
        or not get_config(message.server.id, "misc", "translate_enable")
    ):
        return

    translation = deepl.Translator(config.deepl_key, send_platform_info=False)
    usage = translation.get_usage()

    if usage.any_limit_reached:
        await message.reply(
            content="Unable to translate message: monthly limit reached.",
            mention=False,
        )
        return

    out_flag = ""
    out_name = ""

    output = translation.translate_text(
        message.content,
        target_lang=langs[emoji_id]["code"],
    )
    if output.detected_source_lang == "EN":
        out_flag = "🇺🇸"
        out_name = "English"
    elif output.detected_source_lang == "PT":
        out_flag = "🇵🇹"
        out_name = "Portuguese"
    else:
        for v in langs:
            if langs[v]["code"] == output.detected_source_lang:
                out_flag = v
                out_name = langs[v]["name"]

    embed = revolt.SendableEmbed(
        title=f"Translated from {out_name} by {user.original_avatar}",
        description=output.text,
        icon_url=user.avatar.url if user.avatar else None,
        url=message_to_url(message),
    )

    await message.reply(embed=embed, mention=False)


def setup(bot):
    return Messagescan(bot)
