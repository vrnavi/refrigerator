import json
import re
import discord
import datetime
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.checks import check_if_staff, check_if_bot_manager


class Messagescan(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_re = re.compile(
            r"https://(?:canary\.|ptb\.)?discord\.com/channels/[0-9]+/[0-9]+/[0-9]+",
            re.IGNORECASE,
        )
        self.twitterlink_re = re.compile(
            r"https://twitter\.com/[A-z0-9]+/status/[0-9]+",
            re.IGNORECASE,
        )
        self.prevmessages = {}

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def snipe(self, ctx):
        if ctx.channel.id in self.prevmessages:
            lastmsg = self.prevmessages[ctx.channel.id]
            # Prepare embed msg
            embed = discord.Embed(
                color=ctx.author.color,
                description=f"{lastmsg.content}",
                timestamp=lastmsg.created_at,
            )
            embed.set_footer(
                text=f"Sniped by {ctx.author.name}#{ctx.author.discriminator}"
            )
            embed.set_author(
                name=f"💬 {lastmsg.author.name}#{lastmsg.author.discriminator} said in #{lastmsg.channel.name}...",
                icon_url=f"{lastmsg.author.display_avatar.url}",
            )
            await ctx.reply(embed=embed, mention_author=False)
        else:
            await ctx.reply(
                content="There is no message in the snipe cache for this channel.",
                mention_author=False,
            )

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()

        msglinks = self.link_re.findall(message.content)
        twitterlinks = self.twitterlink_re.findall(message.content)
        if not msglinks and not twitterlinks:
            return
        tlinks = None
        embeds = None

        if twitterlinks:
            tlinks = []
            for t in twitterlinks:
                tlinks.append(t[:8] + "vx" + t[8:])
            tlinks = "\n".join(tlinks)

        if msglinks:
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
                    color=rcvmessage.author.color,
                    description=f"{rcvmessage.content}",
                    timestamp=rcvmessage.created_at,
                )
                embed.set_footer(
                    text=f"Quoted by {message.author.name}#{message.author.discriminator}"
                )
                embed.set_author(
                    name=f"💬 {rcvmessage.author.name}#{rcvmessage.author.discriminator} said in #{rcvmessage.channel.name}...",
                    icon_url=f"{rcvmessage.author.display_avatar.url}",
                )
                embeds.append(embed)
        await message.edit(suppress=True)
        await message.reply(content=tlinks, embeds=embeds, mention_author=False)

    @Cog.listener()
    async def on_message_delete(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot:
            return

        self.prevmessages[message.channel.id] = message


async def setup(bot: Bot):
    await bot.add_cog(Messagescan(bot))
