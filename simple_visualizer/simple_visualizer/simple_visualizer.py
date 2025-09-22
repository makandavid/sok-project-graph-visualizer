import json
import os
from api.interfaces.visualizer_plugin import VisualizerPlugin

class SimpleVisualizerPlugin(VisualizerPlugin):
    """
    A visualizer plugin that generates an HTML string with a simple graph visualization.
    """
    def name(self) -> str:
        return "Simple Visualizer"

    def id(self) -> str:
        return "simple_visualizer"

    def visualize(self, graph):
        """
        Generates an HTML string with an embedded D3.js graph visualization.
        """
        here = os.path.dirname(os.path.abspath(__file__))

        js_file_path = os.path.join(here, 'static', 'visualize.js')
        content = open(js_file_path).read()
      
        pieces = content.split("GRAPH_JSON")

        return pieces[0] + json.dumps(graph.to_dict()) + pieces[1]