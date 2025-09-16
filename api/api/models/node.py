import json


class Node(object):
    def __init__(self, id: int, attributes: dict | None = None):
        self.id = id
        self.attribute = attributes

    def __str__(self):
        return "Node ID: {}\nAttributes:\n{}\n".format(self.id, json.dumps(self.attribute, indent=4))