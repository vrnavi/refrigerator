import json

color_list = {}

current_color = []

def get_colors():
    if not color_list:
        with open("data/colors.json", "r") as f:
            return json.load(f)
    else:
        return color_list