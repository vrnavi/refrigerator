import time
import config
import discord
from datetime import datetime, timezone
from discord.ext import commands
from discord.ext.commands import Cog
import aiohttp
import re as ren

class Basic(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        """[U] Says hello!"""
        await ctx.send(f"Hello {ctx.author.mention}! Have you drank your Soylent Green today?")

    @commands.command(aliases=["yt"])
    async def youtube(self, ctx, *, arg:str):
        """[U] returns the first video in youtubes search."""
        try:
            async with aiohttp.ClientSession() as session: #common.aioget spams info with entire reponse body, so am doing this instead
                async with session.get(f'https://www.youtube.com/results?search_query={arg}') as response: #seems to be santized by aiohttp
                    
                    if response.status is not 200:
                        raise ConnectionError
                    
                    html = await response.text()
                    id = ren.findall(r"watch\?v=(\S{11})", html)[0] #finds the first instance of watch\?=[youtube video id]
                    await ctx.send(f"https://www.youtube.com/watch?v={id}")
        except ConnectionError:
            await ctx.send("wh? something broke?")
            
        
    @commands.command()
    async def hug(self, ctx):
        """[U] Gives you a hug."""
        await ctx.send(f"I am incapable of hugs, but... \*hugs*")

    @commands.command()
    async def kill(self, ctx, the_text: str):
        """[U] Kills someone."""
        await ctx.send(
            f"{the_text} got stuck in the Dishwasher."
        )

    @commands.command()
    async def avy(self, ctx, target = None):
        """[U] Gets an avy."""
        if target is not None:
            # In the case of IDs.
            try:
                user = await ctx.guild.fetch_member(int(target))
            # In the case of mentions.
            except ValueError:
                user = await ctx.guild.fetch_member(target[2:-1])
            # In the case of no user.
            except discord.NotFound:
                user = await self.bot.fetch_user(int(target))
        else:
                user = ctx.author
        await ctx.send(content=user.display_avatar.url)

    @commands.command()
    async def install(self, ctx):
        """[U] Teaches you how to install a Dishwasher."""
        await ctx.send(
            f"Here's how to install a dishwasher:\n<https://www.whirlpool.com/blog/kitchen/how-to-install-a-dishwasher.html>\n\nWhile you're at it, consider protecting your dishwasher:\n<https://www.2-10.com/homeowners-warranty/dishwasher/>\n\nRemember, the more time you spend with your dishwasher instead of the kitchen sink, __the better__."
        )

    @commands.cooldown(1, 10, type=commands.BucketType.user)
    @commands.command(name="hex")
    async def _hex(self, ctx, num: int):
        """[U] Converts base 10 to 16."""
        hex_val = hex(num).upper().replace("0X", "0x")
        await ctx.send(f"{ctx.author.mention}: {hex_val}")

    @commands.cooldown(1, 10, type=commands.BucketType.user)
    @commands.command(name="dec")
    async def _dec(self, ctx, num):
        """[U] Converts base 16 to 10."""
        await ctx.send(f"{ctx.author.mention}: {int(num, 16)}")

    @commands.guild_only()
    @commands.command()
    async def membercount(self, ctx):
        """[U] Prints the member count of the server."""
        await ctx.send(f"{ctx.guild.name} has {ctx.guild.member_count} members!")

    @commands.command(hidden=True)
    async def about(self, ctx):
        """[U] Shows a quick embed with bot info."""
        embed = discord.Embed(
            title="Dishwasher", url=config.source_url, description=config.embed_desc
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["commands"])
    async def help(self, ctx):
        """Posts a help command."""
        await ctx.send("[Press F1 For] HELP\nhttps://os.whistler.page/F1")

    @commands.command(aliases=["p"])
    async def ping(self, ctx):
        """[U] Shows ping values to discord.

        RTT = Round-trip time, time taken to send a message to discord
        GW = Gateway Ping"""
        before = time.monotonic()
        tmp = await ctx.send("Calculating ping...")
        after = time.monotonic()
        rtt_ms = (after - before) * 1000
        gw_ms = self.bot.latency * 1000

        message_text = f":ping_pong:\nrtt: `{rtt_ms:.1f}ms`\ngw: `{gw_ms:.1f}ms`"
        self.bot.log.info(message_text)
        await tmp.edit(content=message_text)

    @commands.guild_only()
    @commands.command()
    async def info(self, ctx, target = None):
        """[S] Gets full user info."""
        if target == None:
            target = ctx.author
        else:
            # target handler
            # In the case of IDs.
            try:
                target_id = int(target)
                target = await self.bot.fetch_user(target_id)
            # In the case of mentions.
            except ValueError:
                target = await self.bot.fetch_user(target[2:-1])

        if target.bot:
            isbot = " [BOT]"
        else:
            isbot = ""

        if ctx.guild.get_member(target.id) is None:
            # Memberless code.
            color = discord.Color.lighter_gray()
            usertype = "user"
            nickname = ""
        else:
            # Member code.
            target = ctx.guild.get_member(target.id)
            color = target.color
            usertype = "member"
            nickname = f"\n**Nickname:** `{target.nick}`"
            
        embed = discord.Embed(
            color=color, title=f"Statistics for {usertype} @{target}{isbot}", description=f"**ID:** `{target.id}`{nickname}", timestamp=datetime.now()
        )
        embed.set_footer(text="Dishwasher")
        embed.set_author(name=f"{target}", icon_url=f"{target.display_avatar.url}")
        embed.set_thumbnail(url=f"{target.display_avatar.url}")
        embed.add_field(
            name="⏰ Account created:",
            value=f"<t:{target.created_at.astimezone().strftime('%s')}:f>\n<t:{target.created_at.astimezone().strftime('%s')}:R>",
            inline=True
        )
        if ctx.guild.get_member(target.id) is not None:
            embed.add_field(
                name="⏱️ Account joined:",
                value=f"<t:{target.joined_at.astimezone().strftime('%s')}:f>\n<t:{target.joined_at.astimezone().strftime('%s')}:R>",
                inline=True
            )
            embed.add_field(
                name="🗃️ Joinscore:",
                value=f"`{sorted(ctx.guild.members, key=lambda v: v.joined_at).index(target)+1}` of `{len(ctx.guild.members)}`",
                inline=True
            )
            emoji=""
            details=""
            name=""
            try:
                if target.activity.emoji is not None:
                    emoji=f"{target.activity.emoji} "
            except:
                pass
            try:
                if target.activity.details is not None:
                    details=f"\n{target.activity.details}"
            except:
                pass
            try:
                if target.activity.name is not None:
                    name=f"{target.activity.name}"
            except:
                pass
            embed.add_field(
                name="💭 Status:",
                value=f"{emoji}{name}{details}",
                inline=False
            )
            roles = []
            for index, role in enumerate(target.roles):
                if role.name == "@everyone":
                    continue
                roles.append("<@&" + str(role.id) + ">")
                rolelist = ",".join(reversed(roles))
            embed.add_field(
                name=f"🎨 Roles:",
                value=f'{rolelist}',
                inline=False
            )

        await ctx.reply(
            embed=embed,
            mention_author=False
        )


async def setup(bot):
    await bot.add_cog(Basic(bot))
