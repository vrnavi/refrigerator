import random
import config


def random_self_msg(authorname):
    return random.choice(config.target_self_messages).format(authorname=authorname)


def random_bot_msg(authorname):
    return random.choice(config.target_bot_messages).format(authorname=authorname)
