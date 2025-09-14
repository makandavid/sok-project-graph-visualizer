import json

from .edge import Edge
from .node import Node


class Graph(object):
    def __init__(self, nodes: list, edges: list):
        self.nodes = nodes
        self.edges = edges

    def _exists(self, node_id: int) -> bool:
        for node in self.nodes:
            if node.id == node_id:
                return True
        return False   
    
    def add_node(self, node_id, attributes) -> bool:
        if not self._exists(node_id):
            self.nodes.append(Node(node_id, attributes))
            return True
        return False
    
    def add_edge(self, edge_id: int, source: Node, target: Node, attributes) -> bool:
        if self._exists(source.id) and self._exists(target.id):
            self.edges.append(Edge(edge_id, source, target, attributes))
            return True
        return False
    
    def to_json_string(self) -> str:
        return json.dumps(self.__dict__, default=lambda o: o.__dict__, indent=4)