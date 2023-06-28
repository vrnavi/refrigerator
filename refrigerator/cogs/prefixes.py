import json
import config
from revolt.ext import commands
import revolt
from helpers.userdata import get_userprefix, fill_userdata, set_userdata


class CogPrefixes(commands.Cog):
    """
    Commands for letting users manage their custom prefixes.
    """

    def __init__(self, bot):
        self.qualified_name = "prefixes"
        self.bot = bot

    @commands.group(aliases=["prefix"])
    async def prefixes(self, ctx: commands.Context):
        """[U] Lists all prefixes."""
        embed = revolt.embed.SendableEmbed(
            title="Your current prefixes...", description=""
        )

        uid = str(ctx.author.id)
        userprefixes = get_userprefix(uid)

        if (len(userprefixes)) == 0:
            await ctx.message.reply("You do not have any prefixes set.", mention=False)
            return

        for i in range(min(config.maxprefixes, len(userprefixes))):
            embed.description += f"**{i + 1}.** {userprefixes[i]}"
            if (i + 1) < len(userprefixes):
                embed.description += "\n"
        await ctx.message.reply(embed=embed, mention=False)

    @prefixes.command()
    async def add(self, ctx: commands.Context, *, arg: str):
        userdata, uid = fill_userdata(ctx.author.id)
        print(userdata)
        if not len(userdata[uid]["prefixes"]) >= config.maxprefixes:
            userdata[uid]["prefixes"].append(f"{arg} ")
            set_userdata(json.dumps(userdata))
            await ctx.message.reply(content="Prefix added.", mention=False)
        else:
            await ctx.message.reply(
                content=f"You have reached your limit of {config.maxprefixes} prefixes.",
                mention=False,
            )

    @prefixes.command()
    async def remove(self, ctx: commands.Context, num: str):
        # making num an int will throw an error.
        # so it has to be passed as a string and then converted to an int.
        number: int
        try:
            number = int(num)
        except ValueError:
            await ctx.message.reply(
                content="This prefix does not exist.", mention=False
            )
            return

        """[U] Removes a prefix."""
        userdata, uid = fill_userdata(ctx.author.id)
        userdata[uid]["prefixes"]
        try:
            userdata[uid]["prefixes"].pop(number - 1)
            set_userdata(json.dumps(userdata))
            await ctx.message.reply(content="Prefix removed.", mention=False)
        except IndexError:
            await ctx.message.reply(
                content="This prefix does not exist.", mention=False
            )


def setup(bot: commands.CommandsClient):
    return CogPrefixes(bot)
