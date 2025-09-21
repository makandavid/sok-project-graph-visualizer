import json
from django.apps.registry import apps
from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.contrib import messages
import tempfile
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


from api.models.graph import Graph
from api.services.search_filter import search, filter

def index(request: HttpRequest):
    app_config = apps.get_app_config('graph_explorer')
    visualization_plugins = app_config.visualization_plugins
    data_source_plugins = app_config.data_source_plugins
    
    g = Graph([], [])
    json_data_source = None
    
    for plugin in data_source_plugins:
        if plugin.id() == "json_data_source":
            json_data_source = plugin
            break
    
    if json_data_source:
        try:
            g = json_data_source.load_data("../json_data_source/data/test.json")
            print(f"Loaded graph with {len(g.nodes)} nodes and {len(g.links)} links")
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Error loading JSON data: {e}")
            g = create_fallback_graph()
    else:
        print("No JSON data source plugin found, using fallback data")
        g = create_fallback_graph()
    
    app_config.current_graph = g
    app_config.filtered_graph = g
    app_config.applied_filters = []
    
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
            json_data = data.get('json_data')
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_file.write(json.dumps(json_data))
                temp_file_path = temp_file.name
            
            app_config = apps.get_app_config('graph_explorer')
            json_data_source = None
            for plugin in app_config.data_source_plugins:
                if plugin.id() == "json_data_source":
                    json_data_source = plugin
                    break

            if json_data_source:
                g = json_data_source.load_data(temp_file_path)
                app_config.current_graph = g
                app_config.filtered_graph = g
                app_config.applied_filters = []

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
                return JsonResponse({"success": False, "error": "JSON data source plugin not found"})
            
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
    app_config = apps.get_app_config('graph_explorer')
    visualization_plugins = app_config.visualization_plugins
    data_source_plugins = app_config.data_source_plugins
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
                filter_str = f"{request.GET["attr"]} {ops[request.GET["op"]]} {request.GET["val"]}"

            if visualization_plugins:
                visualization_script = visualization_plugins[0].visualize(g)
                app_config.filtered_graph = g
                applied_filters.append(filter_str)
        
        except Exception:
            error_message = "Filter error: Can't compare different types!"
           
    return render(request, "index.html", {
        "visualization_plugins": visualization_plugins,
        "visualization_script": visualization_script,
        "data_source_plugins": data_source_plugins,
        "error_message": error_message,
        "applied_filters": applied_filters,
    })  

def reset_filter(request: HttpRequest):
    app_config = apps.get_app_config('graph_explorer')
    visualization_plugins = app_config.visualization_plugins
    data_source_plugins = app_config.data_source_plugins

    visualization_script = ""
    if visualization_plugins:
        visualization_script = visualization_plugins[0].visualize(app_config.current_graph)
        app_config.filtered_graph = app_config.current_graph
        app_config.applied_filters = []
           
    return render(request, "index.html", {
        "visualization_plugins": visualization_plugins,
        "visualization_script": visualization_script,
        "data_source_plugins": data_source_plugins,
        "applied_filters": [],
    })   

def change_visualization_plugin(request: HttpRequest):
    app_config = apps.get_app_config('graph_explorer')
    visualization_plugins = app_config.visualization_plugins
    data_source_plugins = app_config.data_source_plugins
    applied_filters = app_config.applied_filters

    visualization_script = ""

    if request.method == 'GET':
        print(request.GET)
        viz_id = request.GET["id"]
        for viz in visualization_plugins:
            if viz.id() == viz_id and visualization_plugins:
                visualization_script = visualization_plugins[0].visualize(app_config.filtered_graph)
                break

    return render(request, "index.html", {"data_source_plugins": data_source_plugins,
                                          "visualization_plugins": visualization_plugins,
                                          "visualization_script": visualization_script,
                                          "applied_filters": applied_filters,})