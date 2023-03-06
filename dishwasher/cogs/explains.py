import discord
import config
from discord.ext import commands
from discord.ext.commands import Cog


class Explains(Cog):
    """
    Commands for easily explaining certain things.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True, aliases=["memechannel", "wherememes", "memes"])
    async def dumpster(self, ctx):
        """Explains Dumpster."""
        await ctx.send("**Where can I meme?/Why is there no meme channel?**\nA while ago, there was a channel for memes called Dumpster. It was removed due to misuse. Dumpster has not, is not, and will never be a core part of this server, and it is not coming back.\n\n**Please keep memes out of this server. <#256926147827335170> and <#256970699581685761> are NOT substitute meme channels.**")
        
    @commands.command(hidden=True, aliases=["embeds", "howpostembeds", "embed", "emoji"])
    async def journal(self, ctx):
        """Explains Strange Journal and Camera."""
        await ctx.send("**How do I post embeds?/Why cant I use [emoji/stickers]?**\nTo post embeds, react to messages, post emoji or stickers, or speak in voice channels, you need the Strange Journal role. To do any of the prior in <#256926147827335170>, you'll need the Camera role.\nTo learn how to get these roles, read <#989959374900449380>.\n\n**Do __not__ \"spoonfeed\" any user the command for them (e.g. \"just use X command!)\". Doing so may result in a warning.**")
        
    @commands.command(hidden=True, aliases=["howappeal", "howtoappeal"])
    async def appeal(self, ctx):
        """Explains how to appeal."""
        await ctx.send("**To appeal a ban, use the following link.**\nhttp://os.whistler.page/appeal\n\nThis link can also be found on the pinned Steam Discussions post, and on the external site at https://os.whistler.page.")

async def setup(bot):
    await bot.add_cog(Explains(bot))
