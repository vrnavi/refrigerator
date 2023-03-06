# This Cog contains code from Archiver, which was made by Roadcrosser.
# https://github.com/Roadcrosser/archiver
import discord
import json
import os
import httplib2
import re
import datetime
import config
import asyncio
import zipfile

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO

from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff
from helpers.userlogs import userlog
from helpers.store import DECISION_EMOTES, LAST_UNROLEBAN

class ModArchive(Cog):
    def __init__(self, bot):
        self.bot = bot
        roleban_channels = config.toss_channels
        
    async def log_whole_channel(self, channel, zip_files=False):
        st = ""

        if zip_files:
            b = BytesIO()
            z = zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED)
            zipped_count = 0
            
        async for m in channel.history(limit=None):
            blank_content = True
            ts = "{:%Y-%m-%d %H:%M} ".format(m.created_at)
            padding = len(ts) + len(m.author.name) + 2
            add = ts
            if m.type == discord.MessageType.default:
                add += "{0.author.name}: {0.clean_content}".format(m)
                if m.clean_content:
                    blank_content = False
            else:
                add += m.system_content
                
            for a in m.attachments:
                if not blank_content:
                    add += "\n"
                add += " " * (padding * (not blank_content)) + "Attachment: " + a.filename
                if zip_files:
                    fn = "{}-{}-{}".format(m.id, a.id, a.filename)
                    async with self.bot.session.get(a.url) as r:
                        f = await r.read()

                    z.writestr(fn, f)
                    add += " (Saved as {})".format(fn)
                    zipped_count += 1

                blank_content = False
                
            for e in m.embeds:
                if e.type == "rich":
                    if not blank_content:
                        add += "\n"
                    add += textify_embed(
                        e, limit=40, padding=padding, pad_first_line=not blank_content
                    )
                    blank_content = False
                    
            if m.reactions:
                if not blank_content:
                    add += "\n"
                add += " " * (padding * (not blank_content))
                add += " ".join(
                    ["[{} {}]".format(str(r.emoji), r.count) for r in m.reactions]
                )
                blank_content = False

            add += "\n"
            st = add + st

        ret = st
        if zip_files:
            if zipped_count:
                z.writestr("log.txt", st)
                b.seek(0)
                ret = (ret, b)
            else:
                ret = (ret, None)

        return ret
    
    def is_rolebanned(self, member, hard=True):
        roleban = [r for r in member.guild.roles if r.id == config.toss_role_id]
        if roleban:
            if config.toss_role_id in [r.id for r in member.roles]:
                if hard:
                    return (
                        len(
                            [
                                r
                                for r in member.roles
                                if not (r.managed)
                            ]
                        )
                        == 2
                    )
                return True
        
    async def get_members(self, message, args):
        user = []
        if args:
            user = message.guild.get_member_named(args)
            if not user:
                user = []
                arg_split = args.split()
                for a in arg_split:
                    try:
                        a = int(a.strip("<@!#>"))
                    except:
                        continue
                    u = message.guild.get_member(a)
                    if not u:
                        try:
                            u = await self.bot.fetch_user(a)
                        except:
                            pass
                    if u:
                        user += [u]
            else:
                user = [user]

        return (user, None)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["archives"])
    async def archive(self, ctx, *, args = ""):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "data/service_account.json", "https://www.googleapis.com/auth/drive"
        )
        credentials.authorize(httplib2.Http())
        gauth = GoogleAuth()
        gauth.credentials = credentials
        drive = GoogleDrive(gauth)
        folder = config.drive_folder
        message = ctx.message

        try:
            await message.channel.typing()
        except:
            pass
            
        if message.channel.id in config.toss_channels:
            out = await self.log_whole_channel(message.channel, zip_files=True)
            zipped_files = out[1]
            out = out[0]
            
            user = "unspecified (logged by {})".format(message.author.name)
            if (
                (not args)
                and LAST_UNROLEBAN.is_set
                and LAST_UNROLEBAN.diff(message.created_at) < config.unroleban_expiry
            ):
                args = str(LAST_UNROLEBAN.user_id)
                LAST_UNROLEBAN.unset()

            if args:
                user = await self.get_members(message, args)
                if user[0]:
                    user = " ".join(["{} {}".format(u.name, u.id) for u in user[0]])
                else:
                    user = args
                    
            fn = "{:%Y-%m-%d} {}".format(message.created_at, user)

            reply = "📕 Archived as: `{}.txt`".format(fn)

            out += "{:%Y-%m-%d %H:%M} {}: {}".format(
                message.created_at, self.bot.user.name, reply
            )
            
            modch = self.bot.get_channel(config.staff_channel)

            f = drive.CreateFile(
                {
                    "parents": [{"kind": "drive#fileLink", "id": folder}],
                    "title": fn + ".txt",
                }
            )
            f.SetContentString(out)
            f.Upload()

            ret_string = (
                "{} archive saved as [`{}.txt`](https://drive.google.com/file/d/{})".format(
                    message.channel.mention, fn, f["id"]
                )
            )

            if zipped_files:
                f_zip = drive.CreateFile(
                    {
                        "parents": [{"kind": "drive#fileLink", "id": folder}],
                        "title": fn + " (files).zip",
                    }
                )
                f_zip.content = zipped_files
                f_zip["mimeType"] = "application/zip"
                f_zip.Upload()

                ret_string += "\nFiles saved as [`{} (files).zip`](https://drive.google.com/file/d/{})".format(
                    fn, f_zip["id"]
                )

            await message.channel.send(reply)
            await modch.send(
                embed=discord.Embed(description=ret_string, color=message.guild.me.color)
            )

            return True
        else:
            limit = 10
            query = "'{}' in parents".format(folder)
            args = re.sub("[^a-zA-Z0-9 ]", "", args) if args else None
            title = "Results"
            if not args:
                await message.channel.send(
                    "Error: Unable to search archives. Please specify arguments."
                )
                return

            search_term = args

            query += " and title contains '{}'".format(search_term)
            title += " for " + search_term

            fl = drive.ListFile({"q": query}).GetList()
            fl_count = len(fl)
            unlisted_fl_count = fl_count - limit
            fl = fl[:limit]
            msg = "No Results."
            if fl:
                msg = "\n".join(
                    [
                        "[`{title}`](https://drive.google.com/file/d/{id})".format(**f)
                        for f in fl
                    ]
                )
                if unlisted_fl_count > 0:
                    msg += f"\nand **{unlisted_fl_count}** more..."
            await message.channel.send(
                embed=discord.Embed(
                    title=title,
                    url="https://drive.google.com/drive/folders/{}".format(folder),
                    description=msg,
                    color=message.guild.me.color,
                )
            )
    
        return True
        

    @Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id == config.guild_usage and self.is_rolebanned(member):
            LAST_UNROLEBAN.set(
                member.id, datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            )
        
    @Cog.listener()
    async def on_member_update(self, before, after):
        if (
            before.guild.id == config.guild_usage
            and self.is_rolebanned(before)
            and not self.is_rolebanned(after)
        ):
            LAST_UNROLEBAN.set(
                after.id, datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            )
            
async def setup(bot):
    await bot.add_cog(ModArchive(bot))
