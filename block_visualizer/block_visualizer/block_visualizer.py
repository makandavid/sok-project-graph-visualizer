import json
import os
from api.interfaces.visualizer_plugin import VisualizerPlugin
from api.utils.custom_json_encoder import CustomJSONEncoder

class BlockVisualizerPlugin(VisualizerPlugin):
    
    def name(self) -> str:
        return "Block Visualizer"

    def id(self) -> str:
        return "block_visualizer"

    def visualize(self, graph):
        here = os.path.dirname(os.path.abspath(__file__))
        content = open(os.path.join(here, 'static', 'visualize.js')).read()
        pieces = content.split("GRAPH_JSON")
        return pieces[0]+json.dumps(graph.to_dict(), cls=CustomJSONEncoder)+pieces[1]