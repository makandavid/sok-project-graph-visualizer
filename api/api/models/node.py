import json
from datetime import date, datetime

from ..services.utils import DateTimeEncoder, sanitize_dates

class Node(object):
    def __init__(self, id: int, attributes: dict | None = None):
        self.id = id
        self.attributes = attributes

    def __str__(self):
        return f"Node ID: {self.id}\nAttributes:\n{json.dumps(self.attributes, cls=DateTimeEncoder, indent=4)}\n"
    
    def to_dict(self):
        return {"id": self.id, "attributes": None if self.attributes is None else sanitize_dates(self.attributes)}
    
    @staticmethod
    def from_dict(data):
        return Node(data['id'], data['attributes'])