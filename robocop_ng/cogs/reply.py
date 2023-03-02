import discord
from discord.ext.commands import Cog
import json
import re
import config
import datetime
from helpers.restrictions import get_user_restrictions
from helpers.checks import check_if_staff


class Reply(Cog):
    """
    Niche functions the OneShot Discord uses.
    """

    def __init__(self, bot):
        self.bot = bot
        self.last_eval_result = None
        self.previous_eval_code = None

    # I don't know! I got this code from the GARBAGE.
    async def handle_message_with_reference(self, message):
        reference_author = message.reference.resolved.author
        if reference_author.id is not message.author.id:
            if reference_author in message.mentions:
                reference_author_has_no_reply_pings_role = reference_author.get_role(1059460475588448416) is not None
                if reference_author_has_no_reply_pings_role:
                    author_is_staff = (message.author.get_role(259199371361517569) or message.author.get_role(256985367977263105)) is not None
                    if author_is_staff == False:
                        await message.add_reaction("🗞️")
                        await message.reply("\n".join([
                            f"**{message.author.display_name}, do not reply ping users who don't want to be pinged.**",
                            "Please check if a user has a `No Reply Pings` role on them before pinging them in replies.",
                            "You can turn off reply pings by using the blue `@ ON` button to the right of the message bar.",
                            "",
                            "__Ignoring this message repeatedly will lead to a server warning!__"
                        ]), delete_after=10, mention_author=True)

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        
        if message.reference is not None:
            await self.handle_message_with_reference(message)

async def setup(bot):
    await bot.add_cog(Reply(bot))
