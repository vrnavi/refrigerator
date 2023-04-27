import discord
from discord.ext import commands, tasks
from discord.ext.commands import Cog
import json
import re
import datetime
import random
from helpers.checks import check_if_staff
from helpers.configs import get_misc_config, config_check


class Cotd(Cog):
    """
    A Color of The Day system.
    """

    def __init__(self, bot):
        self.bot = bot
        self.colortimer.start()
        self.nocfgmsg = "CoTD isn't set up for this server."
        self.colors = json.load(open("assets/colors.json", "r"))

    def cog_unload(self):
        self.colortimer.cancel()

    @commands.guild_only()
    @commands.command()
    async def cotd(self, ctx):
        if not config_check(ctx.guild.id, "cotd"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        cotd_role = ctx.guild.get_role(get_misc_config(ctx.guild.id, "cotd_role"))
        inlist = False
        cotdlist = ""
        for i in self.colors:
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
        if not config_check(ctx.guild.id, "cotd"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        color = random.choice(self.colors)
        cotd_role = ctx.guild.get_role(get_misc_config(ctx.guild.id, "cotd_role"))
        cotd_name = get_misc_config(ctx.guild.id, "cotd_name")
        await cotd_role.edit(
            name=f'{cotd_name} - {color["name"]}',
            color=discord.Colour.from_str(f'{color["hex"]}'),
            reason=f'Color of The Day: {color["name"]}',
        )
        await ctx.reply(
            content=f"The CoTD has been changed to **{color['name']}** *{color['hex']}*."
        )

    @tasks.loop(time=datetime.time(hour=5, tzinfo=datetime.timezone.utc))
    async def colortimer(self):
        await self.bot.wait_until_ready()
        for g in self.bot.guilds:
            if config_check(g.id, "cotd"):
                color = random.choice(self.colors)
                cotd_name = get_misc_config(g.id, "cotd_name")
                cotd_role = g.get_role(get_misc_config(g.id, "cotd_role"))
                await cotd_role.edit(
                    name=f'{cotd_name} - {color["name"]}',
                    color=discord.Colour.from_str(color["hex"]),
                    reason=f'Color of The Day: {color["name"]}',
                )


async def setup(bot):
    await bot.add_cog(Cotd(bot))
