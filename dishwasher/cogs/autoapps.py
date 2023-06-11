import discord
from discord.ext.commands import Cog
import json
import re
import config
from datetime import datetime
from datetime import timezone
from helpers.checks import check_if_staff
from helpers.sv_config import get_config


class AutoApps(Cog):
    """
    Automatic application responses with per-guild variance.
    """

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()

        if (
            message.guild
            and get_config(message.guild.id, "autoapp", "enable")
            and message.channel.id
            == get_config(message.guild.id, "autoapp", "autoapp_channel")
            and message.author.id
            == get_config(message.guild.id, "autoapp", "autoapp_id")
        ):
            custom_msg = (
                "\n" + get_config(message.guild.id, "autoapp", "autoapp_msg") + "\n"
                if get_config(message.guild.id, "autoapp", "autoapp_msg")
                else ""
            )
            staledays = (
                get_config(message.guild.id, "autoapp", "autoapp_staledays") * 86400
            )
            staff_thread_name = (
                user + "'s " + get_config(message.guild.id, "autoapp", "autoapp_name")
            )
            # Guild specific code.
            if (
                message.guild.id == 256926147827335170
                and message.embeds[0].fields[2].value is not None
            ):
                user = await self.bot.fetch_user(message.embeds[0].fields[2].value[:-5])
                custom_msg = (
                    "\n"
                    + f"Until it can be coded to automatically appear here, use `pws logs {message.embeds[0].fields[2].value}`.\nRemember to post ban context if available (ban record, modmail logs, etc.)."
                    + "\n"
                )
            elif message.guild.id == 363821745590763520 and message.embeds is not None:
                user = await self.bot.fetch_user(message.content.split()[-1][:-1])
                thread = await message.guild.get_channel(
                    1117253103700430868
                ).create_thread(
                    name=message.embeds[0].fields[2].value,
                    type=discord.ChannelType.private_thread,
                    reason=f"Automatic Applications by {self.bot.user.name}.",
                    invitable=False,
                )
                await thread.add_user(user.id)
                await thread.send(
                    content=f"{user.mention}, this thread is for the discussion of your submitted character `{message.embeds[0].fields[2].value}` with the GMs."
                )
            else:
                user = message.author

            await message.add_reaction("✅")
            await message.add_reaction("❎")
            await message.add_reaction("✳️")
            appthread = await message.create_thread(
                name=staff_thread_name,
                reason=f"Automatic Applications by {self.bot.user.name}.",
            )
            staff_role = message.guild.get_role(
                get_config(message.guild.id, "staff", "staff_role")
            )
            await appthread.send(
                content=f"Vote using reactions. Use this thread for discussion.\n`✅ = Yes`\n`❎ = No`\n`✳️ = Abstain`\n{custom_msg}\nThere are currently `{int(len(staff_role.members))}` Staff members at this time.\nVoting should end once one option reaches `{int(len(staff_role.members)/2//1+1)}` votes.\n\nThis appeal will turn stale on <t:{int(datetime.now(timezone.utc).timestamp())+staledays}:f>, or <t:{int(datetime.now(timezone.utc).timestamp())+staledays}:R>."
            )


async def setup(bot):
    await bot.add_cog(AutoApps(bot))
