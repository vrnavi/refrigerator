import json
import discord
import config
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.userdata import get_userprefix, fill_userdata, set_userdata

class prefixes(Cog):
    """
    Commands for letting users manage their custom prefixes.
    """

    def __init__(self, bot):
        self.bot = bot
        

    @commands.group(aliases=["prefix"], invoke_without_command=True)
    async def prefixes(self, ctx):
        """Lists off prefixes"""
        embed = discord.Embed(title="Active Prefixes", description="mentioning the bot will always be a prefix !", colour=10724259)
        embed.set_author(icon_url=ctx.author.display_avatar.url, name=ctx.author.display_name)
        uid = str(ctx.author.id)
        userprefixes = get_userprefix(uid)
        
        for i in range(config.maxprefixes): #max of 24 prefixes as discord does not allow more than 25 fields
            try:
                value = userprefixes[i]
            except (IndexError, TypeError):
                value = "---"
            finally:
                embed.add_field(name=i, value=f"- {value}")
        embed.set_footer(text="use ``prefix add/remove`` to change your prefixes.")
        await ctx.send(embed=embed)

    @prefixes.command()
    async def add(self, ctx, arg:str):
        """adds a new prefix"""
        userdata, uid = fill_userdata(ctx.author.id)
        print(userdata)
        if not len(userdata[uid]["prefixes"]) > config.maxprefixes:
            userdata[uid]["prefixes"].append(f"{arg} ")
            set_userdata(json.dumps(userdata))
            await ctx.send("new prefix set")
        else: ctx.send(f"you have reached the max of [{config.maxprefixes}]")


        
    @prefixes.command()
    async def remove(self, ctx, arg:int):
        userdata, uid = fill_userdata(ctx.author.id)
        userdata[uid]["prefixes"]
        try:
            userdata[uid]["prefixes"].pop(arg)
            set_userdata(json.dumps(userdata))
            await ctx.send("prefix removed")
        except IndexError: 
            await ctx.send("what do you want me to remove?") 
    
async def setup(bot):
    await bot.add_cog(prefixes(bot))