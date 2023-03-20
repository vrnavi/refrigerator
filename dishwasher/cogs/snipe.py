import json
import discord
import config
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff, check_if_bot_manager


class snipe(Cog):
    """
    Used to recover quickly deleted messages.
    """

    def __init__(self, bot):
        self.bot = bot
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
            await ctx.reply(content="There is no message in the snipe cache for this channel.", mention_author=False)

    @Cog.listener()
    async def on_message_delete(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot:
            return

        self.prevmessages[message.channel.id] = message


async def setup(bot):
    await bot.add_cog(snipe(bot))
