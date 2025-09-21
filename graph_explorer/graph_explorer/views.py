import json
from django.apps.registry import apps
from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.contrib import messages
import tempfile
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import xml.etree.ElementTree as ET


from api.models.graph import Graph


def index(request: HttpRequest):
    app_config = apps.get_app_config('graph_explorer')
    visualization_plugins = app_config.visualization_plugins
    data_source_plugins = app_config.data_source_plugins

    g = Graph([], [])
    data_source = None

    for plugin in data_source_plugins:
        if plugin.id() in ["json_data_source", "xml_data_source"]:
            data_source = plugin
            break

    if data_source:
        try:
            if data_source.id() == "json_data_source":
                g = data_source.load_data("../json_data_source/data/test.json")
            elif data_source.id() == "xml_data_source":
                g = data_source.load_data("../xml_data_source/data/test.xml")
            print(f"Loaded graph with {len(g.nodes)} nodes and {len(g.links)} links")
        except (FileNotFoundError, json.JSONDecodeError, ET.ParseError, KeyError) as e:
            print(f"Error loading data: {e}")
            g = create_fallback_graph()
    else:
        print("No data source plugin found, using fallback data")
        g = create_fallback_graph()

    app_config.current_graph = g

    if visualization_plugins:
        visualization_script = visualization_plugins[0].visualize(g)
    else:
        visualization_script = ""

    return render(request, "index.html", {
        "visualization_plugins": visualization_plugins,
        "visualization_script": visualization_script,
        "data_source_plugins": data_source_plugins
    })


@csrf_exempt
def upload_graph(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            file_type = data.get("type")
            content = data.get("data")

            if not content or not file_type:
                return JsonResponse({"success": False, "error": "No data or type provided"})

            suffix = ".json" if file_type == 'json' else '.xml'
            plugin_id = 'json_data_source' if file_type == 'json' else 'xml_data_source'

            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as temp_file:
                if file_type == 'json':
                    temp_file.write(json.dumps(content))
                else:
                    temp_file.write(content)
                temp_file_path = temp_file.name

            app_config = apps.get_app_config('graph_explorer')
            selected_plugin = None
            for plugin in app_config.data_source_plugins:
                if plugin.id() == plugin_id:
                    selected_plugin = plugin
                    break

            if selected_plugin:
                g = selected_plugin.load_data(temp_file_path)

                app_config.current_graph = g

                vis_script = app_config.visualization_plugins[0].visualize(g) if app_config.visualization_plugins else ""

                # Clean up
                os.unlink(temp_file_path)

                return JsonResponse({
                    "success": True,
                    "visualization_script": vis_script,
                    "node_count": len(g.nodes),
                    "link_count": len(g.links)
                })
            else:
                return JsonResponse({"success": False, "error": f"{plugin_id} not found"})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


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
