import os
import time
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
import asyncio
import aiohttp
import re as ren
import revolt
from revolt.ext import commands

import config
from helpers.checks import check_only_server


class CogBasic(commands.Cog):
    def __init__(self, bot: commands.CommandsClient):
        self.qualified_name = "basic"
        self.bot = bot
        matplotlib.use("agg")

    @commands.command(aliases=["hi", "hey"])
    async def hello(self, ctx: commands.Context):
        """[U] Says hello!"""
        await ctx.message.reply(
            f"Hello {ctx.author.display_name}! Have you drank your Soylent Green today?",
            mention=False,
        )

    @commands.command(aliases=["yt"])
    async def youtube(self, ctx: commands.Context, *, arg: str):
        """[U] Returns the first video in a YouTube search."""
        try:
            async with aiohttp.ClientSession() as session:  # common.aioget spams info with entire reponse body, so am doing this instead
                async with session.get(
                    f"https://www.youtube.com/results?search_query={arg}"
                ) as response:  # seems to be santized by aiohttp
                    if response.status != 200:
                        raise ConnectionError

                    html = await response.text()
                    id = ren.findall(r"watch\?v=(\S{11})", html)[
                        0
                    ]  # finds the first instance of watch\?=[youtube video id]
                    await ctx.send(f"https://www.youtube.com/watch?v={id}")
        except ConnectionError:
            await ctx.message.reply("wh? something broke?", mention=False)

    @commands.command()
    async def hug(self, ctx: commands.Context):
        """[U] Gives you a hug."""
        await ctx.message.reply(
            f"I am incapable of hugs, but... \*hugs*", mention=False
        )

    @commands.command()
    async def kill(self, ctx: commands.Context, the_text: str):
        """[U] Kills someone."""
        await ctx.send(f"{the_text} got stuck in the Dishwasher.")

    @commands.command()
    async def eggtimer(self, ctx: commands.Context, minutes: str = "5"):
        """[S] Posts a timer."""
        if int(minutes) >= 60:
            return await ctx.message.reply(
                "I'm not making a timer longer than an hour.", mention=False
            )
        time = int(minutes) * 60
        await ctx.message.add_reaction("⏳")
        await asyncio.sleep(time)
        msg = await ctx.channel.send(content=ctx.author.mention)
        await msg.edit(content=":hourglass:")
        await asyncio.sleep(5.0)
        await msg.delete()

    @commands.command()
    async def avy(self, ctx: commands.Context, target: str = None):
        """[U] Gets an avy."""
        if target is not None:
            if ctx.server and target == "server":
                await ctx.message.reply(ctx.server.icon.url, mention=False)
                return
            if ctx.server and ctx.server.get_member(target):
                target = ctx.server.get_member(target)
        else:
            target = ctx.author
        await ctx.message.reply(content=target.avatar.url, mention=False)

    @commands.command()
    async def install(self, ctx: commands.Context):
        """[U] Teaches you how to install a Dishwasher."""
        await ctx.message.reply(
            "Here's how to install a dishwasher:\n"
            "<https://www.whirlpool.com/blog/kitchen/how-to-install-a-dishwasher.html>\n\n"
            "While you're at it, consider protecting your dishwasher:\n"
            "<https://www.2-10.com/homeowners-warranty/dishwasher/>\n\n"
            "Remember, the more time you spend with your dishwasher instead of the kitchen sink, __the better__.",
            mention=False,
        )

    @commands.command(name="hex")
    async def _hex(self, ctx: commands.Context, num: str):
        """[U] Converts base 10 to 16."""
        hex_val = hex(int(num)).upper().replace("0X", "0x")
        await ctx.message.reply(f"Result: `{hex_val}`", mention=False)

    @commands.command(name="dec")
    async def _dec(self, ctx: commands.Context, num: str):
        """[U] Converts base 16 to 10."""
        await ctx.message.reply(f"Result: `{int(num, 16)}`", mention=False)

    @commands.command(aliases=["catbox", "imgur"])
    async def rehost(self, ctx: commands.Context, links: str = None):
        """[U] Uploads a file to catbox.moe."""
        api_url = "https://catbox.moe/user/api.php"
        if not ctx.message.attachments and not links:
            await ctx.message.reply(
                "You need to supply a file or a file link to rehost.", mention=False
            )
            return
        links = links.split() if links else []
        for r in [f.url for f in ctx.message.attachments] + links:
            formdata = aiohttp.FormData()
            formdata.add_field("reqtype", "urlupload")
            if config.catbox_key:
                formdata.add_field("userhash", config.catbox_key)
            formdata.add_field("url", r)
            async with self.bot.session.post(api_url, data=formdata) as response:
                output = await response.text()
                await ctx.message.reply(content=output, mention=False)

    @commands.check(check_only_server)
    @commands.command()
    async def membercount(self, ctx: commands.Context):
        """[U] Prints the member count of the server."""
        await ctx.message.reply(
            f"{ctx.server.name} has {len(ctx.server.members)} members!", mention=False
        )

    @commands.command()
    async def about(self, ctx: commands.Context):
        """[U] Shows a quick embed with bot info."""
        embed = revolt.SendableEmbed(
            title=self.bot.user.name,
            description=config.embed_desc,
            url=config.source_url,
            icon_url=self.bot.user.original_avatar.url,
            colour="#9cd8df",
        )
        await ctx.message.reply(embed=embed, mention=False)

    @commands.command(name="server", aliases=["invite"])
    async def hostserver(self, ctx: commands.Context):
        """[U] Gives an invite to the host server."""
        # TODO: Revolt does not allow DMing users by bots right now...
        return
        await ctx.author.send(
            content="Here is an invite to my host server.\nhttps://discord.gg/"
            + "p"
            + "3"
            + "M"
            + "v"
            + "p"
            + "S"
            + "v"
            + "X"
            + "r"
            + "m"
        )
        if ctx.server:
            await ctx.message.reply(
                "As to not be rude, I have DMed the server link to you.", mention=False
            )

    @commands.command(aliases=["commands"])
    async def help(self, ctx: commands.Context):
        """[U] Posts a help command."""
        await ctx.message.reply(
            "[Press F1 For] HELP\n" "https://0ccu.lt/dishwasher/commands/",
            mention=False,
        )

    @commands.command(aliases=["showcolor"])
    async def color(self, ctx: commands.Context, color: str = None):
        """[U] Shows a color in chat."""

        if not color:
            await ctx.message.reply(
                "Please provide a hexadecimal color as argument.", mention=False
            )
            return

        if color[0] == "#":
            color = color[1:]

        def hex_check(color):
            try:
                int(color, 16)
                return True
            except ValueError:
                return False

        if hex_check(color) and len(color) == 6:
            await ctx.message.reply(
                f"https://singlecolorimage.com/get/{color}/128x128",
                mention=False,
            )
        else:
            await ctx.message.reply(
                "Please provide a valid hexadecimal color.", mention=False
            )

    @commands.command(aliases=["p"])
    async def ping(self, ctx: commands.Context):
        """[U] Shows ping values to discord.

        RTT = Round-trip time, time taken to send a message to discord
        GW = Gateway Ping"""
        # TODO: revolt.py bot client does not have `latency` attribute...
        return
        before = time.monotonic()
        tmp = await ctx.message.reply("⌛", mention=False)
        after = time.monotonic()
        rtt_ms = (after - before) * 1000
        gw_ms = self.bot.latency * 1000

        message_text = f":ping_pong:\nrtt: `{rtt_ms:.1f}ms`\ngw: `{gw_ms:.1f}ms`"
        self.bot.log.info(message_text)
        await tmp.edit(content=message_text)

    @commands.check(check_only_server)
    @commands.command()
    async def poll(self, ctx: commands.Context, poll_title: str, *options: str):
        poll_emoji = [
            "1️⃣",
            "2️⃣",
            "3️⃣",
            "4️⃣",
            "5️⃣",
            "6️⃣",
            "7️⃣",
            "8️⃣",
            "9️⃣",
            "🔟",
        ]
        optionlines = ""
        if not options:
            await ctx.message.reply(
                content="**No options specified.** Add some and try again.",
                mention=False,
            )
            return
        elif len(options) > 10:
            await ctx.message.reply(
                content="**Too many options.** Remove some and try again.",
                mention=False,
            )
        for i, l in enumerate(options):
            if l[-1:] == '"' and l[:1] == '"':
                optionlines = f"{optionlines}\n`#{i+1}:` {l[1:-1]}"
            elif (l[-1:] == '"' or l[:1] == '"') and not (
                l[-1:] == '"' and l[:1] == '"'
            ):
                await ctx.message.reply(
                    content="**Malformed poll options.** Check your quotes.",
                    mention=False,
                )
                return
            else:
                optionlines = f"{optionlines}\n`#{i+1}:` {l}"
        poll = await ctx.message.reply(
            content=f"**{poll_title}**{optionlines}", mention=False
        )
        for n in range(len(options)):
            await poll.add_reaction(poll_emoji[n])

    # @commands.cooldown(1, 5, type=commands.BucketType.default)
    @commands.check(check_only_server)
    @commands.command(aliases=["loadingbar"])
    async def progressbar(self, ctx: commands.Context):
        """[U] Creates a progress bar of the current year."""
        start = datetime(datetime.now().year, 1, 1)
        end = datetime(datetime.now().year + 1, 1, 1)
        total = end - start
        current = datetime.now() - start
        percentage = (current / total) * 100

        plt.figure().set_figheight(0.5)
        plt.margins(x=0, y=0)
        plt.tight_layout(pad=0)
        plt.axis("off")
        plt.barh(0, percentage, color="#43b581")
        plt.barh(0, 100 - percentage, left=percentage, color="#747f8d")
        plt.margins(x=0, y=0)
        plt.tight_layout(pad=0)
        plt.axis("off")
        plt.savefig(f"{ctx.server.id}-progressbar.png")
        plt.close()

        await ctx.message.reply(
            content=f"**{datetime.now().year}** is **{percentage}**% complete.",
            attachments=[revolt.File(f"{ctx.server.id}-progressbar.png")],
            mention=False,
        )
        os.remove(f"{ctx.server.id}-progressbar.png")

    # @commands.cooldown(1, 5, type=commands.BucketType.default)
    @commands.check(check_only_server)
    @commands.command()
    async def joingraph(self, ctx: commands.Context):
        """[U] Shows the graph of users that joined."""
        rawjoins = [m.joined_at.date() for m in ctx.server.members]
        joindates = sorted(list(dict.fromkeys(rawjoins)))
        joincounts = []
        for i, d in enumerate(joindates):
            if i != 0:
                joincounts.append(joincounts[i - 1] + rawjoins.count(d))
            else:
                joincounts.append(rawjoins.count(d))
        plt.plot(joindates, joincounts)
        plt.savefig(f"{ctx.server.id}-joingraph.png", bbox_inches="tight")
        plt.close()
        await ctx.message.reply(
            attachments=[revolt.File(f"{ctx.server.id}-joingraph.png")], mention=False
        )
        os.remove(f"{ctx.server.id}-joingraph.png")

    @commands.check(check_only_server)
    @commands.command(aliases=["joinscore"])
    async def joinorder(self, ctx: commands.Context, target: str = None):
        """[U] Shows the joinorder of a user."""
        members = sorted(ctx.server.members, key=lambda v: v.joined_at)
        if not target:
            memberidx = members.index(ctx.author) + 1
        elif target.startswith("<@") and target[-1] == ">":
            memberidx = members.index(ctx.server.get_member(target[2:-1])) + 1
        elif ctx.server.get_member(target):
            memberidx = members.index(ctx.server.get_member(target)) + 1
        else:
            memberidx = int(target)
        message = ""
        for idx, m in enumerate(members):
            if memberidx - 6 <= idx <= memberidx + 4:
                message = (
                    f"{message}\n`{idx+1}` **{m.original_name}#{m.discriminator}**"
                    if memberidx == idx + 1
                    else f"{message}\n`{idx+1}` {m.original_name}#{m.discriminator}"
                )
        await ctx.message.reply(content=message, mention=False)

    @commands.check(check_only_server)
    @commands.group(name="info")
    async def info(
        self, ctx: commands.Context, target: commands.MemberConverter = None
    ):
        """[S] Gets full user info."""
        if not target:
            target = ctx.author

        if not ctx.server.get_member(target.id):
            # Memberless code.
            color = "#aaaaaa"
            nickname = ""
        else:
            # Member code.
            target = ctx.server.get_member(target.id)
            if len(target.roles) > 0:
                color = target.roles[-1].color
            else:
                color = "#aaaaaa"
            nickname = f"\n**Nickname:** `{ctx.server.get_member(target.id).nickname}`"

        embed = revolt.SendableEmbed(
            title=f"Info for {'user' if ctx.server.get_member(target.id) else 'member'} {target.original_name}#{target.discriminator}{' [BOT]' if target.bot else ''}",
            description=(
                f"**ID:** `{target.id}`{nickname}\n\n"
                f"⏰ Account created: {target.created_at().strftime('%B %d, %Y %H:%M (%Z)')}\n"
            ),
            colour=color,
            icon_url=target.avatar.url if target.avatar else None,
        )

        if ctx.server.get_member(target.id):
            embed.description += f"⏱️ Account joined: {target.joined_at.strftime('%B %d, %Y %H:%M (%Z)')}\n"
            embed.description += f"🗃️ Joinscore: `{sorted(ctx.server.members, key=lambda v: v.joined_at).index(target) + 1}` of `{len(ctx.server.members)}`"

            if not target.bot and target.status.text:
                embed.description += f"\n💭 Status: {target.status.text}"

            roles = []
            if target.roles:
                for role in target.roles:
                    roles.append(role.name)
                rolelist = ", ".join(reversed(roles))
            else:
                rolelist = "None"
            embed.description += f"\n🎨 Roles: {rolelist}"

        await ctx.message.reply(embed=embed, mention=False)

    @info.command()
    async def role(self, ctx: commands.Context, role: str = None):
        """[S] Gets full role info."""
        if not role:
            await ctx.message.reply(
                "Please provide ULID of server role as argument.", mention=False
            )

        role: revolt.Role = ctx.server.get_role(role)
        role_member_count = 0

        for m in ctx.server.members:
            if role in m.roles:
                role_member_count += 1

        embed = revolt.SendableEmbed(
            title=f"Info for role @{role.name}",
            description=f"**ID:** `{role.id}`\n**Color:** `{str(role.color)}`",
            colour=role.color,
        )
        embed.description += (
            f"\n⏰ Role created: {role.created_at().strftime('%B %d, %Y %H:%M (%Z)')}"
        )
        embed.description += f"\n👥 Role members: {role_member_count}"
        embed.description += f"\n\n🚩 Role flags:"
        embed.description += f"\n**Hoisted:** {str(role.hoist)}"
        embed.description += f"\n**Rank:** {role.rank}"

        await ctx.message.reply(embed=embed, mention=False)

    @info.command(aliases=["guild"])
    async def server(self, ctx: commands.Context):
        """[S] Gets full server info."""
        server = ctx.server

        serverdesc = server.description if server.description else "*(None)*"
        embed = revolt.SendableEmbed(
            title=f"Info for server {server.name}",
            description=f"**ID:** `{server.id}`\n**Owner:** {server.owner.mention}\n**Topic**: {serverdesc}\n",
            colour="#aaaaaa",
            icon_url=server.icon.url if server.icon else None,
        )

        if server.icon:
            embed.description += f"\nServer avatar: [URL]({server.icon.url})"
        if server.banner:
            embed.description += f"\nServer banner: [URL]({server.banner.url})"
        embed.description += "\n"

        tc_count = 0
        vc_count = 0
        for c in server.channels:
            if c.channel_type == revolt.ChannelType.text_channel:
                tc_count += 1
            elif c.channel_type == revolt.ChannelType.voice_channel:
                vc_count += 1

        embed.description += f"\n⏰ Server created: {server.created_at().strftime('%B %d, %Y %H:%M (%Z)')}"
        embed.description += f"\n👥 Server members: {len(server.members)}"
        embed.description += f"\n#️⃣ Counters:"
        embed.description += f"\n**Text Channels:** `{tc_count}`"
        embed.description += f"\n**Voice Channels:** `{vc_count}`"
        embed.description += f"\n**Roles:** `{len(server.roles)}`"
        embed.description += f"\n**Emojis:** `{len(server.emojis)}`"

        await ctx.message.reply(embed=embed, mention=False)


def setup(bot: commands.CommandsClient):
    return CogBasic(bot)
