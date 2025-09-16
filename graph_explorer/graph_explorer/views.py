from django.apps.registry import apps
from django.http import HttpRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from api.models.graph import Graph

def index(request: HttpRequest):
    visualization_plugins = apps.get_app_config('graph_explorer').visualization_plugins
    g = Graph([], [])
    g.add_node(0, {'a': 23, 'b': 56})
    g.add_node(1, {'a': 65, 'b': 47})
    g.add_node(2, {'a': 54, 'b': 45})
    g.add_node(3, {'a': 21, 'b': 21})
    g.add_node(4, {'a': 69, 'b': 56})
    g.add_node(5, {'a': 99, 'b': 96})
    g.add_node(6, {'a': 100, 'b': 56, 'c': 200})
    g.add_link(0, 1, 2)
    g.add_link(1, 1, 4)
    g.add_link(2, 1, 3)
    g.add_link(3, 2, 4)
    g.add_link(4, 3, 2)
    g.add_link(5, 3, 6)
    g.add_link(6, 3, 5)
    g.add_link(7, 4, 0)
    apps.get_app_config('graph_explorer').current_graph = g

    if visualization_plugins:
        visualization_script = visualization_plugins[0].visualize(g)
    else:
        visualization_script = ""
    return render(request, "index.html", {"visualization_plugins": visualization_plugins,
                                          "visualization_script": visualization_script})
