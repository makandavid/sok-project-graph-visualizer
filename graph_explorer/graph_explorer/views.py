import json
from django.apps.registry import apps
from django.http import HttpRequest
from django.shortcuts import render

from api.models.graph import Graph

def index(request: HttpRequest):
    app_config = apps.get_app_config('graph_explorer')
    visualization_plugins = app_config.visualization_plugins
    data_source_plugins = app_config.data_source_plugins
    
    # Try to load data from JSON file using data source plugins
    g = Graph([], [])
    json_data_source = None
    
    # Find JSON data source plugin
    for plugin in data_source_plugins:
        if plugin.id() == "json_data_source":
            json_data_source = plugin
            break
    
    if json_data_source:
        try:
            # Load data from sample JSON file
            g = json_data_source.load_data("../json_data_source/data/large_dataset.json")
            print(f"Loaded graph with {len(g.nodes)} nodes and {len(g.links)} links")
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Error loading JSON data: {e}")
            # Fallback to hardcoded data
            g = create_fallback_graph()
    else:
        print("No JSON data source plugin found, using fallback data")
        g = create_fallback_graph()
    
    app_config.current_graph = g

    if visualization_plugins:
        visualization_script = visualization_plugins[0].visualize(g)
    else:
        visualization_script = ""
    return render(request, "index.html", {"visualization_plugins": visualization_plugins,
                                          "visualization_script": visualization_script})


def create_fallback_graph():
    """Create fallback graph data when no data source plugins are available"""
    g = Graph([], [])
    g.add_node(0, {'a': 23, 'b': 56})
    g.add_node(1, {'a': 65, 'b': 47})
    g.add_node(2, {'a': 54, 'b': 45})
    g.add_node(3, {'a': 21, 'b': 21})
    g.add_node(4, {'a': 69, 'b': 56})
    g.add_node(5, {'a': 99, 'b': 96, 'c': 23})
    g.add_node(6, {'a': 100, 'b': 56, 'c': 200, 'd': 300, 'e': 267})
    g.add_node(7, {'a': 3})
    g.add_link(0, 1, 2)
    g.add_link(1, 1, 4)
    g.add_link(2, 1, 3)
    g.add_link(3, 2, 4)
    g.add_link(4, 3, 2)
    g.add_link(5, 3, 6)
    g.add_link(6, 3, 5)
    g.add_link(7, 4, 0)
    return g
