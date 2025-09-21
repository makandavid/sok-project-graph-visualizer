import json

class Node(object):
    def __init__(self, id: int, attributes: dict | None = None):
        self.id = id
        self.attributes = attributes

    def __str__(self):
        return f"Node ID: {self.id}\nAttributes:\n{json.dumps(self.attributes, indent=4)}\n"
    
    def to_dict(self):
        return {"id": self.id, "attributes": self.attributes}