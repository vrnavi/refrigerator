# This Cog contains code from Archiver, which was made by Roadcrosser.
# https://github.com/Roadcrosser/archiver
import revolt
import json
import os
import httplib2
import re
import datetime
import config
import asyncio
import textwrap
import zipfile

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO

from revolt.ext import commands
from helpers.checks import check_if_staff, check_only_server
from helpers.archive import log_whole_channel, get_members
from helpers.sv_config import get_config


class ModArchive(commands.Cog):
    def __init__(self, bot: revolt.Client):
        self.bot = bot
        self.nocfgmsg = "Archival isn't set up for this server."

    @commands.check(check_only_server)
    @commands.check(check_if_staff)
    @commands.command(aliases=["archives"])
    async def archive(self, ctx: commands.Context, *, args: str):
        if not get_config(ctx.server.id, "archive", "enable"):
            return await ctx.message.reply(self.nocfgmsg, mention=False)
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            "data/service_account.json", "https://www.googleapis.com/auth/drive"
        )
        credentials.authorize(httplib2.Http())
        gauth = GoogleAuth()
        gauth.credentials = credentials
        drive = GoogleDrive(gauth)
        folder = get_config(ctx.server.id, "archive", "drive_folder")

        if ctx.channel.name in get_config(ctx.server.id, "toss", "toss_channels"):
            out = await log_whole_channel(self.bot, ctx.channel, zip_files=True)
            zipped_files = out[1]
            out = out[0]

            user = f"unspecified (logged by {ctx.author.original_name}#{ctx.author.discriminator})"
            users = None
            if args:
                try:
                    users = [
                        await self.bot.fetch_user(uid) for uid in int(args.split())
                    ]
                except:
                    return await ctx.message.reply(
                        content="Fetching the users failed. Either a user ID doesn't exist, or you specified them incorrectly..",
                        mention=False,
                    )
            if not args:
                try:
                    users = [
                        await self.bot.fetch_user(uid)
                        for uid in self.bot.tosscache[ctx.server.id][ctx.channel.name]
                    ]
                except:
                    return await ctx.message.reply(
                        content="The toss cache is empty. Please specify user IDs to archive instead.",
                        mention=False,
                    )
            user = f"{users[0].name} {users[0].id}"

            fn = ctx.message.created_at().strftime("%Y-%m-%d") + " " + str(user)

            reply = f"📕 Archived as: `{fn}.txt`"

            out += f"{ctx.message.created_at().strftime('%Y-%m-%d %H:%M')} {self.bot.user.name}: {reply}"
            if users:
                out += "\nThis toss session had the following users:"
                for u in users:
                    out += f"\n- **{u.display_name}** [{u.original_name}] ({u.id})"

            f = drive.CreateFile(
                {
                    "parents": [{"kind": "drive#fileLink", "id": folder}],
                    "title": fn + ".txt",
                }
            )
            f.SetContentString(out)
            f.Upload()

            modch: revolt.TextChannel = self.bot.get_channel(
                get_config(ctx.server.id, "staff", "staff_channel")
            )

            embed = revolt.SendableEmbed(
                title="📁 Toss Channel Archived",
                description=f"{ctx.channel.name}'s session was archived by {ctx.author.mention} ({ctx.author.id})",
            )

            file_id = f["id"]
            embed.description += f"\n\n🔗 **Text**\n{f'[{fn}.txt](https://drive.google.com/file/d/{file_id})'}"

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

                file_id = f_zip["id"]
                embed.description += f"\n\n📦 **Files**\n{f'[{fn} (files).zip](https://drive.google.com/file/d/{file_id})'}"

            await ctx.send(content=reply)
            await modch.send(embed=embed)

            return True
        else:
            limit = 10
            query = f"'{folder}' in parents"
            args = re.sub("[^a-zA-Z0-9 ]", "", args) if args else None
            title = "Results"
            if not args:
                await ctx.send(
                    "Error: Unable to search archives. Please specify arguments."
                )
                return

            search_term = args

            query += f" and title contains '{search_term}'"
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
            await ctx.send(
                embed=revolt.Embed(
                    title=title,
                    url="https://drive.google.com/drive/folders/{}".format(folder),
                    description=msg,
                )
            )

        return True


def setup(bot):
    return ModArchive(bot)
