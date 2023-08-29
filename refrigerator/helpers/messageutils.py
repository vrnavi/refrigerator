import revolt

def message_to_url(message: revolt.Message):
    return f"https://app.revolt.chat/server/{message.server.id}/channel/{message.channel.id}/{message.id}"


async def get_dm_channel(bot: revolt.Client, user: revolt.User) -> revolt.DMChannel:
    dm = await bot.http.open_dm(user.id)
    return bot.get_channel(dm["_id"])

def create_embed_with_fields(title: str = None, description: str = "", color: str = None, fields: list[tuple[str, str]] = []):
    embed = revolt.SendableEmbed(
        title=title,
        description=description,
    )

    if color:
        embed.colour = color

    for field in fields:
        embed.description += f"\n\n**{field[0]}**\n{field[1]}"

    if description == "" and len(fields) > 0:
        embed.description = embed.description.split("\n", 2)[2]

    return embed
