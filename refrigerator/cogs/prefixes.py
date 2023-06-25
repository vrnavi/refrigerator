import json
import config
from voltage.ext import commands
import voltage
from helpers.userdata import get_userprefix, fill_userdata, set_userdata


class prefixes(commands.SubclassedCog):
    """
    Commands for letting users manage their custom prefixes.
    """

    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.command(aliases=["prefix"])
    async def prefixes(self, ctx):
        """[U] Lists all prefixes."""
        embed = voltage.embed.SendableEmbed(
            title="Your current prefixes...", description=""
        )

        uid = str(ctx.author.id)
        userprefixes = get_userprefix(uid)

        if (len(userprefixes)) == 0:
            await ctx.reply("You do not have any prefixes set.", mention=False)
            return

        for i in range(min(config.maxprefixes, len(userprefixes))):
            embed.description += f"**{i + 1}.** {userprefixes[i]}"
            if (i + 1) < len(userprefixes):
                embed.description += "\n"
        await ctx.reply(embed=embed, mention=False)

    @commands.command()
    async def addprefix(self, ctx, *, arg: str):
        userdata, uid = fill_userdata(ctx.author.id)
        print(userdata)
        if not len(userdata[uid]["prefixes"]) >= config.maxprefixes:
            userdata[uid]["prefixes"].append(f"{arg} ")
            set_userdata(json.dumps(userdata))
            await ctx.reply(content="Prefix added.", mention=False)
        else:
            await ctx.reply(
                content=f"You have reached your limit of {config.maxprefixes} prefixes.",
                mention=False,
            )

    @commands.command()
    async def removeprefix(self, ctx, number: int):
        """[U] Removes a prefix."""
        userdata, uid = fill_userdata(ctx.author.id)
        userdata[uid]["prefixes"]
        try:
            userdata[uid]["prefixes"].pop(number - 1)
            set_userdata(json.dumps(userdata))
            await ctx.reply(content="Prefix removed.", mention=False)
        except IndexError:
            await ctx.reply(content="This prefix does not exist.", mention=False)


def setup(bot, data):
    return prefixes(bot, data)
