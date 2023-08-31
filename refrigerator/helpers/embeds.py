import revolt
import datetime

class SendableFieldedEmbedBuilder:
    """
    Class for creating and manipulating embeds with fields.
    """
    def __init__(self, title: str | None = None, description: str = "", color: str | None = None, fields: list[tuple[str, str]] = []):
        self.title = title
        self.description = description
        self.color = color
        self.fields = fields

    def add_field(self, name: str, value: str):
        self.fields.append((name, value))

    def remove_field(self, index: int):
        self.fields.pop(index)

    def set_field_at(self, index: int, name: str, value: str):
        self.fields[index] = (name, value)

    def build(self):
        embed = revolt.SendableEmbed(
            title=self.title,
            description=self.description,
            colour=self.color
        )

        for field in self.fields:
            embed.description += f"\n\n**{field[0]}**\n{field[1]}"

        if self.description == "" and len(self.fields) > 0:
            embed.description = embed.description.split("\n", 2)[2]

        return embed


def split_content(content: str):
    return list([content[i : i + 1020] for i in range(0, len(content), 1020)])

def slice_embed(embed: SendableFieldedEmbedBuilder, content: str, name: str):
    embed.add_field(
        name=name,
        value="**Message was too long to post!** Split into fragments below.",
    )
    for i, c in enumerate(split_content(content)):
        embed.add_field(
            name=f"🧩 Fragment {i+1}",
            value=f">>> {c}",
        )
