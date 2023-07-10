import revolt


def message_to_url(message: revolt.Message):
    return f"https://app.revolt.chat/server/{message.server.id}/channel/{message.channel.id}/{message.id}"


async def get_dm_channel(bot: revolt.Client, user: revolt.User) -> revolt.DMChannel:
    dm = await bot.http.open_dm(user.id)
    return bot.get_channel(dm["_id"])
