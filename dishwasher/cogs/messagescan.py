import re
import discord
import datetime
import asyncio
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
        self.prevedit_before = {}
        self.prevedit_after = {}

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def snipe(self, ctx):
        if ctx.channel.id in self.prevmessages:
            lastmsg = self.prevmessages[ctx.channel.id]
            # Prepare embed msg
            embed = discord.Embed(
                color=ctx.author.color,
                description=lastmsg.content,
                timestamp=lastmsg.created_at,
            )
            embed.set_footer(
                text=f"Sniped by {ctx.author}",
                icon_url=ctx.author.display_avatar.url,
            )
            embed.set_author(
                name=f"💬 {lastmsg.author} said in #{lastmsg.channel.name}...",
                icon_url=lastmsg.author.display_avatar.url,
            )
            await ctx.reply(embed=embed, mention_author=False)
        else:
            await ctx.reply(
                content="There is no message delete in the snipe cache for this channel.",
                mention_author=False,
            )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def snip(self, ctx):
        if ctx.channel.id in self.prevedit_before:
            lastbeforemsg = self.prevedit_before[ctx.channel.id]
            lastaftermsg = self.prevedit_after[ctx.channel.id]
            # Prepare embed msg
            embed = discord.Embed(
                color=ctx.author.color,
                timestamp=lastaftermsg.created_at,
            )
            embed.set_footer(
                text=f"Snipped by {ctx.author}",
                icon_url=ctx.author.display_avatar.url,
            )
            embed.set_author(
                name=f"💬 {lastaftermsg.author} said in #{lastaftermsg.channel.name}...",
                icon_url=lastaftermsg.author.display_avatar.url,
                url=lastaftermsg.jump_url,
            )
            # Split if too long.
            if len(lastbeforemsg.clean_content) > 1024:
                split_before_msg = list(
                    [
                        lastbeforemsg.clean_content[i : i + 1020]
                        for i in range(0, len(lastbeforemsg.clean_content), 1020)
                    ]
                )
                embed.add_field(
                    name=f"❌ Before on <t:{lastbeforemsg.created_at.astimezone().strftime('%s')}:f>",
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
                    ctr = ctr + 1
            else:
                embed.add_field(
                    name=f"❌ Before on <t:{lastbeforemsg.created_at.astimezone().strftime('%s')}:f>",
                    value=f">>> {lastbeforemsg.clean_content}",
                    inline=False,
                )
            if len(lastaftermsg.clean_content) > 1024:
                split_after_msg = list(
                    [
                        lastaftermsg.clean_content[i : i + 1020]
                        for i in range(0, len(lastaftermsg.clean_content), 1020)
                    ]
                )
                embed.add_field(
                    name=f"⭕ After on <t:{lastaftermsg.edited_at.astimezone().strftime('%s')}:f>",
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
                    name=f"⭕ After on <t:{lastaftermsg.edited_at.astimezone().strftime('%s')}:f>",
                    value=f">>> {lastaftermsg.clean_content}",
                    inline=False,
                )
            await ctx.reply(embed=embed, mention_author=False)
        else:
            await ctx.reply(
                content="There is no message edit in the snip cache for this channel.",
                mention_author=False,
            )

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if (
            not message.content
            or message.author.bot
            or not message.channel.permissions_for(message.author).embed_links
        ):
            return

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
                    description=f">>> {rcvmessage.clean_content}",
                    timestamp=rcvmessage.created_at,
                )
                embed.set_footer(
                    text=f"Quoted by {message.author}",
                    icon_url=message.author.display_avatar.url,
                )
                embed.set_author(
                    name=f"💬 {rcvmessage.author} said in #{rcvmessage.channel.name}...",
                    icon_url=rcvmessage.author.display_avatar.url,
                    url=rcvmessage.jump_url,
                )
                # Use a single image from post for now.
                if (
                    rcvmessage.attachments
                    and rcvmessage.attachments[0].content_type[:6] == "image/"
                ):
                    embed.set_image(url=rcvmessage.attachments[0].url)
                elif rcvmessage.embeds and rcvmessage.embeds[0].image:
                    embed.set_image(url=rcvmessage.embeds[0].image.url)
                embeds.append(embed)

        if message.guild and message.channel.permissions_for(message.guild.me).manage_messages:
            # Discord SUCKS!!
            if twitterlinks:
                while not message.embeds:
                    await asyncio.sleep(0.1)
            await message.edit(suppress=True)

        def deletecheck(m):
            return m.id == message.id

        reply = await message.reply(content=tlinks, embeds=embeds, mention_author=False)
        try:
            await message.channel.fetch_message(message.id)
        except NotFound:
            await reply.delete()
        try:
            await self.bot.wait_for("message_delete", timeout=600, check=deletecheck)
            await reply.delete()
        except:
            pass

    @Cog.listener()
    async def on_message_delete(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot or not message.guild:
            return

        self.prevmessages[message.channel.id] = message

    @Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        await self.bot.wait_until_ready()
        if message_after.author.bot or not message_after.guild:
            return

        self.prevedit_before[message_after.channel.id] = message_before
        self.prevedit_after[message_after.channel.id] = message_after


async def setup(bot: Bot):
    await bot.add_cog(Messagescan(bot))
