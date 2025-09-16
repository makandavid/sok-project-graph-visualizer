from ..models.graph import Graph
from .base_plugin import BasePlugin


class VisualizerPlugin(BasePlugin):
    def visualize(self, graph: Graph):
        """Visualize the graph in some way"""
        pass