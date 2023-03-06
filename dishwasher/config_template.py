import hashlib
import datetime
import discord
import json

# Basic bot config, insert your token here, update description if you want
prefixes = ["pws ", "dish "]
token = "token-goes-here"
bot_description = "Dishwasher, a spaghetti bot."

# If you forked Dishwasher, put your repo here
source_url = "https://github.com/vrnavi/dishwasher"
rules_url = "https://reswitched.github.io/discord/#rules"

# The bot description to be used in pws about
embed_desc = (
    "Dishwasher is maintained by `renavi`, as a Dishwasher in her kitchen."
    " I am presently washing her dishes. I am also a fork of "
    "[robocop-ng](https://github.com/reswitched/robocop-ng)."
)

# The cogs the bot will load on startup.
 The cogs the bot will load on startup.
initial_cogs = [
    "cogs.common",
    "cogs.admin",
    "cogs.cotd",
    "cogs.explains",
    "cogs.mod",
    "cogs.mod_antiraid",
    "cogs.mod_archive",
    "cogs.mod_oneshot",
    "cogs.mod_observation",
    "cogs.mod_note",
    "cogs.mod_reacts",
    "cogs.mod_userlog",
    "cogs.mod_timed",
    "cogs.mod_watch",
    "cogs.basic",
    "cogs.logs",
    "cogs.logs",
    "cogs.lockdown",
    "cogs.remind",
    "cogs.reply",
    "cogs.dishtimer",
    "cogs.meme",
    "cogs.invites",
]

# The bot will only work in these guilds. The first in the list is considered the "main" guild.
guild_whitelist = [256926147827335170]  # OneShot Discord

# A mapping of role IDs to names.
named_roles = {
    "journal": 303555716109565955,
}

# The bot manager and staff roles
# Bot manager can run eval, exit and other destructive commands!
# Staff can run administrative commands
bot_manager_role_id = 308094715465695243  # Bot Management role.
# Staff role.
staff_role_ids = [
    259199371361517569,
]
# Ex-Staff role.
exstaff_role_ids = [
    491431570251579412,
]
# Tossed/Rolebanned role.
toss_role_id = 257050851611377666

# Various log channels used to log bot and guild's activity
# You can use same channel for multiple log types
# Spylog channel logs suspicious messages or messages by members under watch
# Invites created with .invite will direct to the welcome channel.
log_channel = 1006820351134683186  # dishwasher-log in OneShot
botlog_channel = 1006820351134683186  # dishwasher-log in OneShot
modlog_channel = 1006820351134683186  # dishwasher-log in OneShot
spylog_channel = 1006820351134683186  # dishwasher-log in OneShot
welcome_channel = 989959323771895880  # rules channel in OneShot.
# Staff channel.
staff_channel = 256964111626141706

# These channel entries are used to determine which roles will be given
# access when we unlock them
general_channels = [
    256926147827335170,
    256970699581685761,
    257057492851228674,
    547150473363456020,
    270745381061525504,
    688183601233133650,
    350855217614553088,
    631612006826377226,
    256984616915828738,
    369934580465139712,
    256973430702866437,
    863599748622712872,
]  # Channels everyone can access

# Controls which roles are blocked during lockdown
lockdown_configs = {
    # Used as a default value for channels without a config, defaults to main guild's everyone role.
    "default": {"channels": general_channels, "roles": [guild_whitelist[0]]},
}

# Channels that will be cleaned every minute/hour.
# This feature isn't very good rn.
# See https://github.com/reswitched/robocop-ng/issues/23
minutely_clean_channels = []
hourly_clean_channels = []

# Edited and deletes messages in these channels will be logged
spy_channels = general_channels

# All lower case, no spaces, nothing non-alphanumeric
suspect_words = [
]

# List of words that will be ignored if they match one of the
# suspect_words (This is used to remove false positives)
suspect_ignored_words = [
]
# == Only if you want to use cogs.pin ==
# Used for the pinboard. Leave empty if you don't wish for a gist pinboard.
github_oauth_token = ""

# Channels and roles where users can pin messages
allowed_pin_channels = []
allowed_pin_roles = []

# Channel to upload text files while editing list items. (They are cleaned up.)
list_files_channel = 0

# == Only if you want to use cogs.lists ==
# Channels that are lists that are controlled by the lists cog.
list_channels = []

# == Only if you want to use cogs.sar ==
self_assignable_roles = {
}

# == Only if you want to use cogs.reply ==
noreply_role = 1059460475588448416

# == Only if you want to use cogs.mod_oneshot ==
pingmods_allow = [named_roles["journal"]] + staff_role_ids

# == Only if you want to use cogs.mod_archive ==
# == Make sure to supply service_account.json!
# The Google Drive folder.
drive_folder = "folder_goes_here"
# The toss/roleban channels.
toss_channels = [
    257049714577506305,
]
# The toss/roleban expiry timeout.
unroleban_expiry = 180

# == Only if you want to use cogs.appeal ==
ban_appeal_channel = 402019542345449472
ban_appeal_webhook_id = 402016472878284801

# == Only if you want to use cogs.cotd ==
cotd_role_id = 534976600454725632

# == Only if you want to use cogs.mod_antiraid ==
# Auto-mention threshold (Minimum to fire, inclusive) (set to 0 to disable)
mention_threshold = 5
# Recent join threshold - When reporting auto lockdowns, will also print a list of members who joined in the last n seconds. (set to 0 to disable)
recent_join_threshold = 20
# Announcement messages for lockdown/unlockdown. Set to `null` if unused.
lockdown_annoncement = "All public channels are temporarily restricted."
unlockdown_annoncement = "All public channels are no longer restricted."

# No touch!
placeholders = json.load(open("assets/placeholders.json", "r"))

# Used for the bot's random options.
# Change this to set the playing type.
game_type = discord.ActivityType.listening
# This is a list of all the "games" to play.
game_names = placeholders["games"]
# These appear when doing pws quit.
death_messages = placeholders["deaths"]
# Currently unused.
tarot_cards = placeholders["tarot"]
