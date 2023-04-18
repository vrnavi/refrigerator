class Unroleban:
    def __init__(self):
        self.guild_set = {}

    def unset(self, guild_id):
        del self.guild_set[guild_id]

    def set(self, guild_id, user_id, time):
        self.guild_set[guild_id]["user_id"] = user_id
        self.guild_set[guild_id]["time"] = time

    def diff(self, guild_id, time):
        return (time - self.guild_set[guild_id][time]).total_seconds()

    def isset(self, guild_id):
        try:
            if self.guild_set[guild_id]:
                return True
        except KeyError:
            return False


LAST_UNROLEBAN = Unroleban()

DECISION_EMOTES = ["✅", "❎"]
