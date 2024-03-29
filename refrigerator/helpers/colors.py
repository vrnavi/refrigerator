﻿class colors:
    default = "#000000"
    teal = "#1abc9c"
    dark_teal = "#11806a"
    green = "#2ecc71"
    dark_green = "#1f8b4c"
    blue = "#3498db"
    dark_blue = "#206694"
    purple = "#9b59b6"
    dark_purple = "#71368a"
    magenta = "#e91e63"
    dark_magenta = "#ad1457"
    gold = "#f1c40f"
    dark_gold = "#c27c0e"
    orange = "#e67e22"
    dark_orange = "#a84300"
    red = "#e74c3c"
    dark_red = "#992d22"
    lighter_grey = "#95a5a6"
    dark_grey = "#607d8b"
    light_grey = "#979c9f"
    darker_grey = "#546e7a"
    blurple = "#7289da"
    greyple = "#99aab5"

    # prevent modification of the values in this class
    def __setattr__(self, name, value):
        pass
