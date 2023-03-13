import discord
from discord.ext.commands import Cog
import json
import re
import config
from datetime import datetime
from datetime import timezone
from helpers.restrictions import get_user_restrictions
from helpers.checks import check_if_staff


class Appeal(Cog):
    """
    Automatic responses for the Ban Appeal system.
    """

    def __init__(self, bot):
        self.bot = bot
        self.last_eval_result = None
        self.previous_eval_code = None

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()

        if (
            message.channel.id == config.ban_appeal_channel
            and message.author.id == config.ban_appeal_webhook_id
            and message.embeds[0].fields[1].value is not None
        ):
            await message.add_reaction("✅")
            await message.add_reaction("❎")
            await message.add_reaction("✳️")
            appealthread = await message.create_thread(
                name=f"{message.embeds[0].fields[1].value[:-5]}'s Appeal",
                reason="Automatic Appeal Thread Generating by Dishwasher.",
            )
            staff_role = ctx.guild.get_role(config.staff_role_id)
            await appealthread.send(
                content=f"**Voting has MOVED to the appeal's post itself!**\nVote using reactions. Use this thread for discussion.\n`✅ = Yes`\n`❎ = No`\n`✳️ = Abstain`\n\nUntil it can be coded to automatically appear here, use `pws logs {message.embeds[0].fields[2].value}`.\nRemember to post ban context if available (ban record, modmail logs, etc.).\n\nThere are currently `{int(len(staff_role.members))}` Staff members at this time.\nVoting should end once one option reaches `{int(len(staff_role.members)/2//1+1)}` votes.\n\nThis appeal will turn stale on <t:{int(datetime.now(timezone.utc).timestamp())+604800}:f>, or <t:{int(datetime.now(timezone.utc).timestamp())+604800}:R>."
            )


async def setup(bot):
    await bot.add_cog(Appeal(bot))
