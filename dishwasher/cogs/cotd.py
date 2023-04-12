import discord
from discord.ext import commands, tasks
from discord.ext.commands import Cog
import json
import re
import config
import datetime
import random
from helpers.checks import check_if_staff


class Cotd(Cog):
    """
    A bootleg Color of The Day system. No persistency.
    """

    def __init__(self, bot):
        self.bot = bot
        self.colortimer.start()

    def cog_unload(self):
        self.colortimer.cancel()

    @commands.guild_only()
    @commands.command()
    async def cotd(self, ctx):
        colors = json.load(open("assets/colors.json", "r"))
        cotd_role = self.bot.get_guild(config.guild_whitelist[0]).get_role(
            config.cotd_role_id
        )
        inlist = False
        cotdlist = ""
        for i in colors:
            if i["hex"] == "#%02x%02x%02x".upper() % cotd_role.color.to_rgb():
                inlist = True
                color = i["hex"]
                cotdlist = f"{cotdlist}\n**{i['name']}** *{i['hex']}*"
        if inlist == False:
            await ctx.send(content="The CoTD role's color is not in the color list!")
        embed = discord.Embed(
            title=f"🌈 Today's CoTD is...",
            description=f"{cotdlist}",
            color=discord.Colour.from_str(color),
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(
            text=f"{self.bot.user.name}'s Color of The Day",
            icon_url=self.bot.user.display_avatar.url,
        )
        embed.set_image(url=f"https://singlecolorimage.com/get/{color[1:]}/128x128")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def reroll(self, ctx):
        colors = json.load(open("assets/colors.json", "r"))
        color = random.choice(colors)
        cotd_role = self.bot.get_guild(config.guild_whitelist[0]).get_role(
            config.cotd_role_id
        )
        await cotd_role.edit(
            name=f'Fluctuating Phosphor - {color["name"]}',
            color=discord.Colour.from_str(f'{color["hex"]}'),
            reason=f'Color of The Day: {color["name"]}',
        )
        await ctx.reply(
            content=f"The CoTD has been changed to **{color['name']}** *{color['hex']}*."
        )

    @tasks.loop(time=datetime.time(hour=5, tzinfo=datetime.timezone.utc))
    async def colortimer(self):
        await self.bot.wait_until_ready()
        colors = json.load(open("assets/colors.json", "r"))
        color = random.choice(colors)
        cotd_role = self.bot.get_guild(config.guild_whitelist[0]).get_role(
            config.cotd_role_id
        )
        await cotd_role.edit(
            name=f'Fluctuating Phosphor - {color["name"]}',
            color=discord.Colour.from_str(f'{color["hex"]}'),
            reason=f'Color of The Day: {color["name"]}',
        )


async def setup(bot):
    await bot.add_cog(Cotd(bot))
