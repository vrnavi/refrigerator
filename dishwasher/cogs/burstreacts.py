import json
from typing import Dict
import discord
import config
from discord.ext import commands
from helpers.configs import get_misc_config


class CogBurstReacts(commands.Cog, name="Burst reactions handler"):
    def __init__(self, bot: commands.Bot):
        """
        Discord Super Reactions autoremover.
        By hat_kid (https://github.com/thehatkid)
        """
        self.bot = bot

    async def burst_reaction_check(self, payload: Dict):
        """Super Reaction handler."""
        channel_id = payload["channel_id"]
        user_id = payload["user_id"]
        message_id = payload["message_id"]
        guild_id = payload.get("guild_id", None)
        emoji = discord.PartialEmoji(
            id=payload["emoji"]["id"], name=payload["emoji"]["name"]
        )
        burst = payload["burst"]

        # Ignore not super reactions or DM reaction add events
        if not burst or not guild_id:
            return

        # Ignore not configured guilds
        if not get_misc_config(int(guild_id), "burstreacts_enable"):
            return

        guild = self.bot.get_guild(int(guild_id))
        channel = guild.get_channel_or_thread(int(channel_id))
        author = guild.get_member(int(user_id))
        message = channel.get_partial_message(int(message_id))

        # Remove reaction
        await message.remove_reaction(emoji, author)

        # Send information to log channel
        mlog = await self.bot.fetch_channel(
            config.guild_configs[guild.id]["logs"]["mlog_thread"]
        )

        embed = discord.Embed(
            title="🗑️ Autoremoved a Super Reaction",
            description=f"{author}`'s {emoji} was removed. [{message.jump_url}]",
            colour=0xEA50BA,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(
            name=f"{self.bot.escape_message(author)}",
            icon_url=f"{author.display_avatar.url}",
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)

        await mlog.send(embed=embed)

    @commands.Cog.listener()
    async def on_socket_raw_receive(self, msg: str):
        """Raw gateway socket events receiver."""
        msg_json = json.loads(msg)
        opcode = msg_json["op"]
        event = msg_json["t"]
        data = msg_json["d"]

        if opcode == 0:
            if event == "MESSAGE_REACTION_ADD":
                await self.burst_reaction_check(data)


async def setup(bot: commands.Bot):
    await bot.add_cog(CogBurstReacts(bot))
