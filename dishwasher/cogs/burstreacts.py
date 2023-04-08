import json
from typing import Dict
import discord
from discord.ext import commands


class CogBurstReacts(commands.Cog, name='Burst reactions handler'):
    def __init__(self, bot: commands.Bot):
        """
        Discord Super Reactions autoremover.
        By hat_kid (https://github.com/thehatkid)
        """
        self.bot = bot

    async def burst_reaction_check(self, payload: Dict):
        """Super Reaction handler."""
        channel_id = payload['channel_id']
        user_id = payload['user_id']
        message_id = payload['message_id']
        guild_id = payload.get('guild_id', None)
        emoji = discord.PartialEmoji(
            id=payload['emoji']['id'],
            name=payload['emoji']['name']
        )
        burst = payload['burst']

        # Ignore not super reactions or DM reaction add events
        if not burst or not guild_id:
            return

        # Ignore not whitelisted guilds
        if int(guild_id) not in self.bot.config.guild_whitelist:
            return

        guild = self.bot.get_guild(int(guild_id))
        channel = guild.get_channel_or_thread(int(channel_id))
        author = guild.get_member(int(user_id))
        message = channel.get_partial_message(int(message_id))

        # Remove reaction
        await message.remove_reaction(emoji, author)

        # Send information to log channel
        log_channel = self.bot.get_channel(self.bot.config.log_channel)

        embed = discord.Embed(
            title=':wastebasket: Super Reaction autoremove',
            description=f'Removing "{emoji}" Super Reaction from message',
            colour=0xEA50BA,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=author.display_avatar.url)
        embed.add_field(name='User', value=f'{author.mention}\n(`{author}`)\nID: `{author.id}`', inline=True)
        embed.add_field(name='Channel', value=f'{channel.mention}\nID: `{channel.id}`', inline=True)
        embed.add_field(name='Message', value=f'> ID: `{message.id}`\n> URL: {message.jump_url}', inline=False)

        if emoji.id:
            # Custom emoji
            embed.add_field(name='Reaction emoji', value=f'> Name: `{emoji.name}`\n> ID: `{emoji.id}`\n> URL: {emoji.url}', inline=False)
        else:
            # Default emoji
            embed.add_field(name='Reaction emoji', value=f'> Unicode: `{emoji.name}`', inline=False)

        view = discord.ui.View(timeout=0.0)
        view.add_item(discord.ui.Button(label='Go to message', url=message.jump_url))

        await log_channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_socket_raw_receive(self, msg: str):
        """Raw gateway socket events receiver."""
        msg_json = json.loads(msg)
        opcode = msg_json['op']
        event = msg_json['t']
        data = msg_json['d']

        if opcode == 0:
            if event == 'MESSAGE_REACTION_ADD':
                await self.burst_reaction_check(data)


async def setup(bot: commands.Bot):
    await bot.add_cog(CogBurstReacts(bot))
