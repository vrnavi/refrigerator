from revolt.ext import commands
from discord.ext import tasks
import revolt
import json
import datetime
import random
from helpers.checks import check_if_staff, check_only_server
from helpers.sv_config import get_config


class Cotd(commands.Cog):
    """
    A Color of The Day system.
    """

    def __init__(self, bot: commands.CommandsClient):
        self.bot = bot
        self.colortimer.start()
        self.voteskip_dict = {}
        self.voteskip_cooldown = []
        self.nocfgmsg = "CoTD isn't set up for this server."
        self.colors = json.load(open("assets/colors.json", "r"))

    def cog_unload(self):
        self.colortimer.cancel()

    async def roll_colors(self, guild: revolt.Server):
        color = random.choice(self.colors)
        cotd_name = get_config(guild.id, "cotd", "cotd_name")
        cotd_role = guild.get_role(get_config(guild.id, "cotd", "cotd_role"))
        await cotd_role.edit(
            name=f'{cotd_name} - {color["name"]}',
            colour=color["hex"]
        )
        return color

    def precedence_check(self, guild: revolt.Server):
        return datetime.datetime.now() > datetime.datetime.now().replace(
            hour=24 - len(self.voteskip[guild.id]), minute=0, second=0
        )

    @commands.check(check_only_server)
    @commands.command()
    async def cotd(self, ctx: commands.Context):
        if not get_config(ctx.server.id, "cotd", "enable"):
            return await ctx.message.reply(self.nocfgmsg)
        cotd_role = ctx.server.get_role(get_config(ctx.server.id, "cotd", "cotd_role"))
        inlist = False
        cotdlist = ""
        for i in self.colors:
            if i["hex"] == cotd_role.colour:
                inlist = True
                color = i["hex"]
                cotdlist = f"{cotdlist}\n**{i['name']}** *{i['hex']}*"
        if inlist == False:
            await ctx.send(content="The CoTD role's color is not in the color list!")
        embed = revolt.SendableEmbed(
            title=f"🌈 Today's CoTD is...",
            description=f"{cotdlist}",
            colour=color,
        )
        embed.icon_url=f"https://singlecolorimage.com/get/{color[1:]}/128x128"
        await ctx.message.reply(embed=embed)

    @commands.check(check_only_server)
    @commands.command()
    async def voteskip(self, ctx: commands.Context):
        if not get_config(ctx.server.id, "cotd", "enable"):
            return await ctx.message.reply(self.nocfgmsg)

        if ctx.server.id in self.voteskip_cooldown:
            return await ctx.message.reply(
                content=f"Sorry, CoTD skipping is on cooldown. Please try again tomorrow.",
            )

        if ctx.server.id not in self.voteskip_dict:
            self.voteskip_dict[ctx.server.id] = []

        if ctx.author.id in self.voteskip_dict[ctx.server.id]:
            timestamp = (
                datetime.datetime.now()
                .replace(hour=24 - len(self.voteskip_dict[ctx.server.id]), minute=0, second=0)
                .strftime("%s")
            )
            return await ctx.message.reply(
                content=f"You have already voted to skip this CoTD.\nRerolling will occur `{len(self.voteskip[ctx.server.id])}` hours earlier on <t:{timestamp}:t>, or <t:{timestamp}:R>.",
            )

        self.voteskip_dict[ctx.server.id].append(ctx.author.id)

        if self.precedence_check(ctx.server):
            self.voteskip[ctx.server.id] = []
            self.voteskip_cooldown.append(ctx.server.id)
            color = await self.roll_colors(ctx.server)
            await ctx.message.reply(
                content=f"Vote to skip the current CoTD has passed.\nThe CoTD has been changed to **{color['name']}** *{color['hex']}*.",
            )
        else:
            timestamp = (
                datetime.datetime.now()
                .replace(hour=24 - len(self.voteskip[ctx.server.id]), minute=0, second=0)
                .strftime("%s")
            )
            await ctx.message.reply(
                content=f"Your vote to skip has been recorded.\nRerolling will occur `{len(self.voteskip[ctx.server.id])}` hours earlier on <t:{timestamp}:t>, or <t:{timestamp}:R>.",
            )

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command()
    async def reroll(self, ctx: commands.Context):
        if not get_config(ctx.server.id, "cotd", "enable"):
            return await ctx.message.reply(self.nocfgmsg)
        color = await self.roll_colors(ctx.server)
        await ctx.message.reply(
            content=f"The CoTD has been changed to **{color['name']}** *{color['hex']}*."
        )

    @tasks.loop(time=[datetime.time(hour=x) for x in range(0, 24)])
    async def colortimer(self):
        for g in self.bot.servers:
            if get_config(g.id, "cotd", "enable"):
                if g.id not in self.voteskip_dict:
                    self.voteskip_dict[g.id] = []
                if self.voteskip_dict[g.id] and self.precedence_check(g):
                    self.voteskip_dict[g.id] = []
                    await self.roll_colors(g)
                elif int(datetime.datetime.now().strftime("%H%M")) == 0000:
                    if g.id in self.voteskip_cooldown:
                        self.voteskip_cooldown.remove(g.id)
                    await self.roll_colors(g)


def setup(bot):
    return Cotd(bot)
