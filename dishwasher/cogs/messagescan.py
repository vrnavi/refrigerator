import json
import re
import discord
import datetime
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands


class Messagescan(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_re = re.compile(r"https://discord\.com/channels/[0-9]+/[0-9]+/[0-9]+", re.IGNORECASE)

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()

        msglinks = self.link_re.findall(message.content)

        if not msglinks:
            return

        embeds = []
        for m in msglinks:
            components = m.split("/")
            guildid = int(components[4])
            channelid = int(components[5])
            msgid = int(components[6])
            
            rcvguild = self.bot.get_guild(guildid)
            rcvchannel = rcvguild.get_channel_or_thread(channelid)
            rcvmessage = await rcvchannel.fetch_message(msgid)
            
            # Prepare embed msg
            embed = discord.Embed(
            color = rcvmessage.author.color,
            description=f"{rcvmessage.content}",
            timestamp=rcvmessage.created_at,
            )
            embed.set_footer(text=f"Quoted by {message.author.name}#{message.author.discriminator}")
            embed.set_author(
                name=f"💬 {rcvmessage.author.name}#{rcvmessage.author.discriminator} said in #{rcvmessage.channel.name}...",
                icon_url=f"{rcvmessage.author.display_avatar.url}",
            )
            embeds.append(embed)        
        await message.reply(embeds=embeds, mention_author=False)

async def setup(bot: Bot):
    await bot.add_cog(Messagescan(bot))
