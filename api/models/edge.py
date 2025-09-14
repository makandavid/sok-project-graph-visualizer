import json

from .node import Node


class Edge(object):
    def __init__(self, id: int, source: Node, target: Node, attributes: dict | None = None):
        self.source = source
        self.target = target
        self.attributes = attributes

    def __str__(self):
        return "Edge ID: {}\nEdge Source: {}\nEdge Target: {}\nAttributes:\n{}\n".format(self.id, self.source, self.target, json.dumps(self.attributes, indent=4))