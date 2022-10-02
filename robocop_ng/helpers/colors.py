import json

color_list = {}

current_color = []

def get_colors():
    if not color_list:
        with open("data/colors.json", "r") as f:
            color_list = json.load(f)
            return color_list
    else:
        return color_list