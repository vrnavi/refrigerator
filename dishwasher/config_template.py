import hashlib
import datetime
import discord
import json

# Basic bot config, insert your token here, update description if you want, put owner IDs, and log channel ID.
prefixes = ["pws ", "dish "]
token = "token-goes-here"
bot_description = "Dishwasher, a spaghetti bot."
bot_managers = [120698901236809728]
bot_logchannel = 1006820351134683186

# If you forked Dishwasher, put your repo here
source_url = "https://github.com/vrnavi/dishwasher"
rules_url = "<#989959323771895880>"

# The bot description to be used in the about command.
embed_desc = (
    "Dishwasher is maintained by `renavi`, as a Dishwasher in her kitchen."
    " I am presently washing her dishes. I am also a fork of "
    "[robocop-ng](https://github.com/reswitched/robocop-ng)."
)

# The cogs the bot will load on startup.
initial_cogs = [
    "cogs.common",
    "cogs.admin",
    "cogs.cotd",
    "cogs.explains",
    "cogs.mod",
    "cogs.mod_appeal",
    "cogs.mod_archive",
    "cogs.mod_locks",
    "cogs.mod_observation",
    "cogs.mod_note",
    "cogs.mod_userlog",
    "cogs.mod_timed",
    "cogs.mod_watch",
    "cogs.basic",
    "cogs.oneshot",
    "cogs.logs",
    "cogs.remind",
    "cogs.reply",
    "cogs.dishtimer",
    "cogs.meme",
    "cogs.invites",
    "cogs.usertime",
    "cogs.prefixes",
    "cogs.burstreacts",
]

# == cogs.prefixes maximum prefixes. ==
maxprefixes = 6  # !max of 24!

# Specific server configuration. Some cogs will default to the first in the list.
guild_configs = {
    # OneShot Discord
    256926147827335170: {
        "logs": {
            # Thread for moderation logs.
            "mlog_thread": 1095159750674624583,
            # Thread for server logs.
            "slog_thread": 1095159988814626966,
            # Thread for user logs.
            "ulog_thread": 1095160504470736987,
        },
        "staff": {
            # Staff role.
            "staff_role": 259199371361517569,
            # Ex-Staff role.
            "exstaff_role": 491431570251579412,
            # Staff channel.
            "staff_channel": 256964111626141706,
            # Rules link.
            "rules_url": "<#989959323771895880>",
            # Appeal link.
            "appeal_url": "https://os.whistler.page/appeal",
            # [cogs.appeal] Ban appeal channel.
            "ban_appeal_channel": 402019542345449472,
            # [cogs.appeal] Ban appeal webhook ID.
            "ban_appeal_webhook_id": 402016472878284801,
            # [cogs.mod_watch] Channel for tracking watched users.
            "tracker_channel": 1095559009152536626,
        },
        "toss": {
            "toss_role": 257050851611377666,
            "toss_channel": 257049714577506305,
            "toss_channels": [
                "basement",
                "abyss",
                "recycle-bin",
                "out-of-bounds",
            ],
        },
        "archive": {
            "drive_folder": "folder_goes_here",
            "unroleban_expiry": 180,
        },
        "anitraid": {
            # [cogs.mod_antiraid] Announcement channels. Set to "all" for all.
            "announce_channels": [256926147827335170],
            # [cogs.mod_antiraid] Mention threshold.
            "mention_threshold": 5,
            # [cogs.mod_antiraid] Recent join threshold.
            "join_threshold": 20,
        },
        "misc": {
            # [cogs.mod_locks/cogs.mod_antiraid] "Authorized" roles.
            "authorized_roles": [303555716109565955],
            # [cogs.mod_locks] "Bot" roles.
            "bot_roles": [256985367977263105],
            # [cogs.cotd] CoTD role.
            "cotd_role": 534976600454725632,
            # [cogs.cotd] CoTD name.
            "cotd_name": "Fluctuating Phosphor",
            # [cogs.reply] No Reply Pings role.
            "noreply_role": 1059460475588448416,
        },
    }
}

# Channels that will be cleaned every minute/hour.
minutely_clean_channels = []
hourly_clean_channels = []

# == Only if you want to use cogs.pin ==
# Used for the pinboard. Leave empty if you don't wish for a gist pinboard.
github_oauth_token = ""
# Channels and roles where users can pin messages
allowed_pin_channels = []
allowed_pin_roles = []


# Used for the bot's random options.
# No touch!
placeholders = json.load(open("assets/placeholders.json", "r"))
# Change this to set the playing type.
game_type = discord.ActivityType.listening
# This is a list of all the "games" to play.
game_names = placeholders["games"]
# These appear when doing pws quit.
death_messages = placeholders["deaths"]
# These appear when the bot tells you not to do a command to itself.
target_bot_messages = placeholders["if_target_bot"]
# These appear when the bot tells you not to do a command to yourself.
target_self_messages = placeholders["if_target_self"]
# Currently unused.
tarot_cards = placeholders["tarot"]
