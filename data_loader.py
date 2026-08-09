import json


def load_json(filepath):  # load data from a JSON file
    with open(filepath, "r") as f:  # open the file in read mode
        data = json.load(f)  # load the JSON data from the file into a Python dictionary
    return data
