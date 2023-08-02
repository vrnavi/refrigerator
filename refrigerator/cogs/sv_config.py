import config
import asyncio
from helpers.checks import check_if_staff, check_if_bot_manager, check_only_server
from revolt.ext import commands
import revolt
from helpers.sv_config import (
    fill_config,
    make_config,
    set_config,
    stock_configs,
    friendly_names,
)


class sv_config(commands.Cog):
    def __init__(self, bot: revolt.Client):
        self.bot = bot

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.group()
    async def configs(self, ctx: commands.Context):
        guild = ctx.server
        configs = fill_config(guild.id)

        navigation_reactions = ["⏹️", "⬅️", "➡️", "⬆️", "⬇️", "⏺️"]

        embed = revolt.SendableEmbed(title="⚙️ Server Configuration Editor", description="⏳ Loading...")
        hindex = 1
        hlimit = len(configs.items())
        vindex = 0
        pagemode = "play"
        configmsg = await ctx.message.reply(embed=embed, mention=False)
        for e in navigation_reactions:
            await configmsg.add_reaction(e)

        def reactioncheck(message: revolt.Message, user: revolt.User, emoji: str):
            return user.id == ctx.author.id and emoji in navigation_reactions

        def messagecheck(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        while True:
            page = list(configs.items())[hindex - 1]
            vlimit = len(page[1])
            embed.description = f"Page `{hindex}` of `{hlimit}` for server {guild.name}.\nTweak a setting with `{config.prefixes[0]}configs set {page[0]} <setting> <value>`."
            lines = ""
            for i, (k, v) in enumerate(page[1].items()):
                friendly = f"**{friendly_names[k]}**\n" if k in friendly_names else ""
                if pagemode == "rec" and vindex == i + 1:
                    setting = f"> **`{k}`**"
                    key = k
                    value = v
                else:
                    setting = f"`{k}`" if vindex != i + 1 else f"> `{k}`"
                if not v and str(v) != "False" and str(v) != "None":
                    v = f"Not Configured ({type(v).__name__})"
                if str(v) == "None":
                    v = "Forcibly Disabled"
                lines += f"\n{friendly}{setting}\n{v}"
            embed.description += "\n\n" + lines
            await configmsg.edit(embeds=[embed])

            if pagemode == "play":
                try:
                    reaction = await self.bot.wait_for(
                        "reaction_add", timeout=30.0, check=reactioncheck
                    )
                except:
                    await ctx.send("Operation timed out.")
                    await configmsg.delete()
                    return

                if reaction[2] == "⏹️":
                    await ctx.send("Operation cancelled.")
                    await configmsg.delete()
                    return
                if reaction[2] == "⬅️":
                    if hindex != 1:
                        hindex -= 1
                    vindex = 0
                    await configmsg.remove_reaction("⬅️", reaction[1])
                elif reaction[2] == "➡️":
                    if hindex != hlimit:
                        hindex += 1
                    vindex = 0
                    await configmsg.remove_reaction("➡️", reaction[1])
                elif reaction[2] == "⬆️":
                    if vindex != 0:
                        vindex -= 1
                    await configmsg.remove_reaction("⬆️", reaction[1])
                elif reaction[2] == "⬇️":
                    if vindex != vlimit:
                        vindex += 1
                    await configmsg.remove_reaction("⬇️", reaction[1])
                elif reaction[2] == "⏺️":
                    pagemode = "rec"
                    await configmsg.remove_reaction("⏺️", reaction[1])
                    continue
            elif pagemode == "rec":
                if configs[page[0]][key] == None:
                    await ctx.send(
                        content="This setting has been administratively disabled by the bot owner. You cannot edit it.",
                        delete_after=5,
                    )
                    pagemode = "play"
                    continue
                editingmsg = f"**Editing** the setting `{key}`.\n\nThis setting is a"
                settingtype = type(configs[page[0]][key]).__name__
                if settingtype == "str":
                    editingmsg += " string. Set this by replying with whatever."
                elif settingtype == "int":
                    editingmsg += "n integer. Set this by replying with a number."
                elif settingtype == "list":
                    editingmsg += " list. Set this by replying with a list of whatevers, separated by spaces."
                elif settingtype == "bool":
                    editingmsg += (
                        " boolean. Set this by replying with `true` or `false`."
                    )
                if value:
                    editingmsg += '\nYou can also reply with "none" to remove the current value, or "stop" to cancel the operation.'
                configsuppmsg = await ctx.send(content=editingmsg)

                try:
                    message = await self.bot.wait_for(
                        "message", timeout=30.0, check=messagecheck
                    )
                except asyncio.TimeoutError:
                    await configsuppmsg.delete()
                    await configmsg.delete()
                    await ctx.send("Operation timed out.")

                if message.content == "stop":
                    await configsuppmsg.delete()
                    await configmsg.delete()
                    await ctx.send("Operation cancelled.")
                elif key == "enable" and message.content == "true":
                    for k, v in configs[page[0]].items():
                        if not v and type(v).__name__ != "bool":
                            await ctx.send(
                                content="This setting cannot be changed unless the other settings in the category are properly configured.\nPlease configure these settings first, then try again."
                            )
                            pagemode = "play"
                            continue

                try:
                    configs = set_config(ctx.server.id, page[0], key, message.content)
                except:
                    await configsuppmsg.edit(
                        content="You gave an invalid value. Please try again while following the instructions of what to send."
                    )
                    pagemode = "play"
                    continue
                else:
                    await configsuppmsg.edit(
                        content=f"**{page[0].title()}/**`{key}` has been updated with a new value of `{configs[page[0]][key]}`."
                    )
                    pagemode = "play"
                    continue

    @commands.check(check_if_bot_manager)
    @configs.command()
    async def reset(self, ctx: commands.Context, guild: revolt.Server = None):
        """[O] Resets the configuration for a guild."""
        if not guild:
            guild = ctx.server
        make_config(guild.id)
        await ctx.message.reply(
            content=f"The configuration for **{guild}** has been reset."
        )

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @configs.command()
    async def set(self, ctx: commands.Context, category: str, setting: str, *, value=None):
        """[S] Sets the configuration for a guild."""
        configs = fill_config(ctx.server.id)
        category = category.lower()
        setting = setting.lower()
        if category not in configs or setting not in configs[category]:
            if category not in stock_configs or setting not in stock_configs[category]:
                return await ctx.message.reply(
                    content="You specified an invalid category or setting."
                )
            else:
                configs = set_config(
                    ctx.server.id, category, setting, stock_configs[category][setting]
                )
        if configs[category][setting] == None:
            return await ctx.message.reply(
                content="This setting has been administratively disabled by the bot owner.",
                mention=True,
            )
        elif configs[category][setting] == "enable" and value == "true":
            for k, v in configs[category].items():
                if not v and type(v).__name__ != "bool":
                    return await ctx.message.reply(
                        content="This setting cannot be changed unless the other settings in the category are properly configured.\nPlease configure these settings first, then try again."
                    )

        try:
            configs = set_config(ctx.server.id, category, setting, value)
            return await ctx.message.reply(
                content=f"**{category.title()}/**`{setting}` has been updated with a new value of `{configs[category][setting]}`."
            )
        except:
            return await ctx.message.reply(
                content="You gave an invalid value. If you don't know what you're doing, use `pls configs` interactively."
            )

    @commands.check(check_if_bot_manager)
    @configs.command()
    async def disable(self, ctx: commands.Context, guild: revolt.Server, category, setting):
        """[O] Forcibly disables a setting for a guild."""
        configs = fill_config(ctx.server.id)
        if category not in configs or setting not in configs[category]:
            configs = set_config(
                ctx.server.id, category, setting, stock_configs[category][setting]
            )
        set_config(ctx.server.id, category, setting, None)
        return await ctx.message.reply(
            content=f"{guild.name}'s **{category.title()}/**`{setting}` has been DISABLED."
        )

    @commands.check(check_if_bot_manager)
    @configs.command()
    async def enable(self, ctx: commands.Context, guild: revolt.Server, category: str, setting: str):
        """[O] Forcibly enables a setting for a guild."""
        configs = fill_config(ctx.server.id)
        if category not in configs or setting not in configs[category]:
            configs = set_config(
                ctx.server.id, category, setting, stock_configs[category][setting]
            )
        defaults = {
            "str": "",
            "bool": False,
            "int": 0,
            "list": [],
        }
        set_config(
            ctx.server.id,
            category,
            setting,
            defaults[type(stock_configs[category][setting]).__name__],
        )
        return await ctx.message.reply(
            content=f"{guild.name}'s **{category.title()}/**`{setting}` has been ENABLED."
        )


def setup(bot: revolt.Client):
    return sv_config(bot)
