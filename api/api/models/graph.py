import json

from .link import Link
from .node import Node


class Graph(object):
    def __init__(self, nodes: list=None, links: list=None):            
        self.nodes = nodes
        self.links = links

        if self.nodes is None:
            self.nodes = []

        if self.links is None:
            self.links = []

    def _exists(self, node_id: int) -> bool:
        for node in self.nodes:
            if node.id == node_id:
                return True
        return False   
    
    def add_node(self, node_id, attributes=None) -> bool:
        if not self._exists(node_id):
            self.nodes.append(Node(node_id, attributes))
            return True
        return False
    
    def add_link(self, link_id: int, source_id: int, target_id: int) -> bool:
        if self._exists(source_id) and self._exists(target_id):
            self.links.append(Link(link_id, source_id, target_id))
            return True
        return False
        
    def to_dict(self):
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "links": [e.to_dict() for e in self.links]
        }