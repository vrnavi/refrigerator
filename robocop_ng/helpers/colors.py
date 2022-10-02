import json
import random

color_list = {}

current_color = {}

def new_random_color():
    global color_list
    if not color_list:
        with open("data/colors.json", "r") as f:
            color_list = json.load(f)
    current_color = random.choice(color_list)
    color_list.remove(current_color)
    return current_color
    
def get_current_color():
    return current_color
    