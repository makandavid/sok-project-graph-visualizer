import json
import os
import tempfile

from api.models.graph import Graph
from api.services.search_filter import search, filter
from django.apps.registry import apps
from django.http import HttpRequest
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .cli import handle_command
from core.use_cases.const import VISUALIZER_GROUP, DATASOURCE_GROUP
from graph_explorer.apps import GraphExplorerConfig


def get_config() -> GraphExplorerConfig:
    return apps.get_app_config('graph_explorer')

def index(request: HttpRequest):
    app_config = get_config()

    # get lists using constants (more general)
    data_source_plugins = app_config.plugin_service.plugins.get(DATASOURCE_GROUP, [])
    visualization_plugins = app_config.plugin_service.plugins.get(VISUALIZER_GROUP, [])

    print(f"Found {len(data_source_plugins)} data source plugins")
    print(f"Found {len(visualization_plugins)} visualization plugins")

    # Build map of plugin id -> supported extensions so the client can update file accept attribute
    plugin_extensions = {plugin.id(): plugin.get_supported_extensions() for plugin in data_source_plugins}

    # Determine selected data source plugin
    selected_plugin_id = request.GET.get('data_source') if request.GET.get('data_source') else (
        data_source_plugins[0].id() if data_source_plugins else None)

    # Use inital sample graph if no data source plugins are available.
    g = create_fallback_graph()

    app_config.current_graph = g
    app_config.filtered_graph = g
    app_config.applied_filters = []

    if visualization_plugins:
        visualization_script = visualization_plugins[0].visualize(g) # in this case block visualier is the default
        app_config.current_visualization_plugin = visualization_plugins[0]
    else:
        visualization_script = ""

    return render(request, "index.html", {
        "visualization_plugins": visualization_plugins,
        "visualization_script": visualization_script,
        "data_source_plugins": data_source_plugins,
        "plugin_extensions_json": json.dumps(plugin_extensions),  # JSON for the client
        "selected_data_plugin": selected_plugin_id,
    })

@csrf_exempt
def upload_graph(request):
    app_config = get_config()
    visualization_plugins = app_config.plugin_service.plugins.get(VISUALIZER_GROUP, [])
    data_source_plugins = app_config.plugin_service.plugins.get(DATASOURCE_GROUP, [])

    if request.method == 'POST':
        temp_file_path = None
        plugin_id = None
        try:
            if request.FILES:
                # accept 'file' (FormData key)
                upload = request.FILES.get('file') or list(request.FILES.values())[0]
                plugin_id = request.POST.get('plugin_id')
                # write uploaded bytes to a temp file
                ext = os.path.splitext(upload.name)[1] or '.tmp'
                with tempfile.NamedTemporaryFile(mode='wb', suffix=ext, delete=False) as tf:
                    for chunk in upload.chunks():
                        tf.write(chunk)
                    temp_file_path = tf.name

            if not plugin_id:
                raise ValueError("Missing plugin_id")

            selected_plugin = next((p for p in data_source_plugins if p.id() == plugin_id), None)
            if not selected_plugin:
                raise ValueError(f"Data source plugin '{plugin_id}' not found")

            # plugin.load_data should know how to parse the file by extension/content
            graph = selected_plugin.load_data(temp_file_path)
            print("Total nodes:", len(graph.nodes), " Total links:", len(graph.links))

            app_config.current_graph = graph
            app_config.filtered_graph = graph
            app_config.applied_filters = []

            vis_script = app_config.current_visualization_plugin.visualize(graph) if visualization_plugins else ""

            try:
                os.unlink(temp_file_path)
            except Exception:
                pass

            return JsonResponse({
                "success": True,
                "visualization_script": vis_script,
                "node_count": len(graph.nodes),
                "link_count": len(graph.links)
            })

        except Exception as e:
            if temp_file_path:
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})

@csrf_exempt
def cli_execute(request: HttpRequest):
    if request.method == "POST":
        data = json.loads(request.body)
        command_str = data.get("command", "")
        app_config = apps.get_app_config("graph_explorer")
        g = app_config.current_graph

        try:
            result = handle_command(g, command_str)
            # Refresh visualization after change
            vis_script = ""
            if app_config.visualization_plugins:
                vis_script = app_config.current_visualization_plugin.visualize(g)

            return JsonResponse({
                "success": True,
                "result": result,
                "visualization_script": vis_script
            })
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

def search_filter(request: HttpRequest):
    app_config = get_config()
    visualization_plugins = app_config.plugin_service.plugins[VISUALIZER_GROUP]
    data_source_plugins = app_config.plugin_service.plugins[DATASOURCE_GROUP]
    applied_filters = app_config.applied_filters

    visualization_script = ""
    filter_str = ""
    error_message = None

    if request.method == 'GET':
        try:
            print(request.GET)
            if "search" in request.GET.keys():
                g = search(app_config.filtered_graph, request.GET["search"])
                filter_str = request.GET["search"]
            else:
                ops = {'eq': '==', 'le': '<=', 'ge': '>=', 'lt': '<', 'gt': '>', 'ne': '!='}
                g = filter(app_config.filtered_graph, request.GET["attr"], ops[request.GET["op"]], request.GET["val"])
                filter_str = f"{request.GET['attr']} {ops[request.GET['op']]} {request.GET['val']}"

            if visualization_plugins:
                visualization_script = app_config.current_visualization_plugin.visualize(g)
                app_config.filtered_graph = g
                applied_filters.append(filter_str)

        except Exception:
            error_message = "Filter error: Can't compare different types!"

    plugin_extensions = {p.id(): p.get_supported_extensions() for p in data_source_plugins}
    selected_plugin_id = request.GET.get('data_source') if request.GET.get('data_source') else (
        data_source_plugins[0].id() if data_source_plugins else None)

    return render(request, "index.html", {
        "visualization_plugins": visualization_plugins,
        "visualization_script": visualization_script,
        "data_source_plugins": data_source_plugins,
        "error_message": error_message,
        "applied_filters": applied_filters,
        "plugin_extensions_json": json.dumps(plugin_extensions),
        "selected_data_plugin": selected_plugin_id,
    })


def reset_filter(request: HttpRequest):
    app_config = get_config()
    visualization_plugins = app_config.plugin_service.plugins[VISUALIZER_GROUP]
    data_source_plugins = app_config.plugin_service.plugins[DATASOURCE_GROUP]

    visualization_script = ""
    if visualization_plugins:
        visualization_script = app_config.current_visualization_plugin.visualize(app_config.current_graph)
        app_config.filtered_graph = app_config.current_graph
        app_config.applied_filters = []

    plugin_extensions = {p.id(): p.get_supported_extensions() for p in data_source_plugins}
    selected_plugin_id = request.GET.get('data_source') if request.GET.get('data_source') else (
        data_source_plugins[0].id() if data_source_plugins else None)

    return render(request, "index.html", {
        "visualization_plugins": visualization_plugins,
        "visualization_script": visualization_script,
        "data_source_plugins": data_source_plugins,
        "applied_filters": [],
        "plugin_extensions_json": json.dumps(plugin_extensions),
        "selected_data_plugin": selected_plugin_id,
    })


def change_visualization_plugin(request: HttpRequest):
    app_config = get_config()
    visualization_plugins = app_config.plugin_service.plugins[VISUALIZER_GROUP]
    data_source_plugins = app_config.plugin_service.plugins[DATASOURCE_GROUP]
    applied_filters = app_config.applied_filters

    visualization_script = ""

    if request.method == 'GET':
        print(request.GET)
        viz_id = request.GET["id"]
        for viz in visualization_plugins:
            if viz.id() == viz_id and visualization_plugins:
                app_config.current_visualization_plugin = viz
                visualization_script = viz.visualize(app_config.filtered_graph)
                break

    plugin_extensions = {p.id(): p.get_supported_extensions() for p in data_source_plugins}
    selected_plugin_id = request.GET.get('data_source') if request.GET.get('data_source') else (
        data_source_plugins[0].id() if data_source_plugins else None)

    return render(request, "index.html", {"data_source_plugins": data_source_plugins,
                                          "visualization_plugins": visualization_plugins,
                                          "visualization_script": visualization_script,
                                          "applied_filters": applied_filters,
                                          "plugin_extensions_json": json.dumps(plugin_extensions),
                                          "selected_data_plugin": selected_plugin_id})