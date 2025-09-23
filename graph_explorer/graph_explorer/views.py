import json
import os
import tempfile
import uuid
from django.views.decorators.csrf import csrf_exempt
from .cli import handle_command

from django.apps.registry import apps
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect

from api.models.graph import Graph
from api.services.search_filter import search, filter

def new_workspace(request: HttpRequest):
    """Creates a new workspace with auto-generated name."""
    workspace_id = str(uuid.uuid4())

    if 'workspaces' not in request.session:
        request.session['workspaces'] = {}

    # Generate default name 
    count = len(request.session['workspaces']) + 1
    workspace_name = f"Workspace #{count}"

    g = create_fallback_graph() 

    request.session['workspaces'][workspace_id] = {
        'name': workspace_name,  
        'graph_data': g.to_dict(),
        'filtered_graph_data': g.to_dict(),
        'applied_filters': [],
        'current_data_source_id': 'json_data_source',
        'current_visualizer_id': 'simple_visualizer'
    }
    request.session.modified = True

    return redirect('index', workspace_id=workspace_id)

def index(request: HttpRequest, workspace_id: str):
    """Displays and manages chosen workspace"""
    app_config = apps.get_app_config('graph_explorer')

    if 'workspaces' not in request.session:
        request.session['workspaces'] = {}
    
    if workspace_id not in request.session['workspaces']:
        print(f"Creating new workspace: {workspace_id}")

        data_source_id = request.GET.get('source', 'json_data_source')
        data_source_plugin = next((p for p in app_config.data_source_plugins if p.id() == data_source_id), None)

        if data_source_plugin:
            try:
                file_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), 
                    '..', data_source_plugin.id(), 'data', 'test.json'
                )
                g = data_source_plugin.load_data(file_path)
            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                print(f"Error loading data from {data_source_id}: {e}")
                g = create_fallback_graph()
        else:
            print(f"No plugin found for ID '{data_source_id}', using fallback data")
            g = create_fallback_graph()

        count = len(request.session['workspaces']) + 1
        request.session['workspaces'][workspace_id] = {
            'name': f"Workspace #{count}", # Default name
            'graph_data': g.to_dict(),
            'filtered_graph_data': g.to_dict(),  # add filtered_graph_data
            'applied_filters': [],
            'current_data_source_id': data_source_id
        }
        request.session.modified = True
    
    workspace_data = request.session['workspaces'][workspace_id]
    g_filtered = Graph.from_dict(workspace_data['filtered_graph_data'])
    
    visualization_plugins = app_config.visualization_plugins
    vis_script = ""
    
    current_visualizer_id = workspace_data.get('current_visualizer_id', 'simple_visualizer')
    selected_visualizer = next((p for p in visualization_plugins if p.id() == current_visualizer_id), None)

    # list of tuples (id, name)
    available_workspaces = [(ws_id, data['name']) for ws_id, data in request.session['workspaces'].items()]

    if selected_visualizer:
        vis_script = selected_visualizer.visualize(g_filtered)

    return render(request, "index.html", {
        "visualization_plugins": visualization_plugins,
        "visualization_script": vis_script,
        "data_source_plugins": app_config.data_source_plugins,
        "current_workspace_id": workspace_id,
        "available_workspaces": available_workspaces,
        "applied_filters": workspace_data['applied_filters'],
        "current_data_source_id": workspace_data.get('current_data_source_id', 'json_data_source') 
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

                vis_script = app_config.current_visualization_plugin.visualize(g) if app_config.visualization_plugins else ""
                
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


def search_filter(request: HttpRequest, workspace_id: str):
    app_config = apps.get_app_config('graph_explorer')
    workspace_data = request.session.get('workspaces', {}).get(workspace_id)
    if not workspace_data:
        return redirect('new_workspace') # Redirect if there is no workspace

    g = Graph.from_dict(workspace_data['filtered_graph_data'])
    
    visualization_plugins = app_config.visualization_plugins
    vis_script = ""
    filter_str = ""
    error_message = None
    
    if request.method == 'GET':
        try:
            print(request.GET)
            if "search" in request.GET.keys():
                g = search(g, request.GET["search"])
                filter_str = request.GET["search"]
            else:
                ops = {'eq': '==', 'le': '<=', 'ge': '>=', 'lt': '<', 'gt': '>', 'ne': '!='}
                g = filter(g, request.GET["attr"], ops[request.GET["op"]], request.GET["val"])
                filter_str = f"{request.GET['attr']} {ops[request.GET['op']]} {request.GET['val']}"

            # Save new filtered graph and filter list to session
            workspace_data['filtered_graph_data'] = g.to_dict()
            workspace_data['applied_filters'].append(filter_str)
            request.session.modified = True

            # Visualise fltered graph
            visualization_plugins = app_config.visualization_plugins
            current_visualizer_id = workspace_data.get('current_visualizer_id', 'simple_visualizer')
            selected_visualizer = next((p for p in visualization_plugins if p.id() == current_visualizer_id), None)
            if selected_visualizer:
                vis_script = selected_visualizer.visualize(g)
        
        except Exception:
            error_message = "Filter error: Can't compare different types!"
            
    available_workspaces = [(ws_id, data.get('name', ws_id[:8])) for ws_id, data in request.session['workspaces'].items()]

    return render(request, "index.html", {
        "visualization_plugins": visualization_plugins,
        "visualization_script": vis_script,
        "data_source_plugins": app_config.data_source_plugins,
        "error_message": error_message,
        "applied_filters": workspace_data['applied_filters'],
        "current_workspace_id": workspace_id,
        "available_workspaces": available_workspaces,
    }) 

# ---

def reset_filter(request: HttpRequest, workspace_id: str):
    workspace_data = request.session.get('workspaces', {}).get(workspace_id)
    if not workspace_data:
        return redirect('new_workspace') # Redirect if there is no workspace

    app_config = apps.get_app_config('graph_explorer')
    visualization_plugins = app_config.visualization_plugins
    
    # Load original unfiltered graph from session
    g_original = Graph.from_dict(workspace_data['graph_data'])

    # Reset filtered_graph and filters in session
    workspace_data['filtered_graph_data'] = g_original.to_dict()
    workspace_data['applied_filters'] = []
    request.session.modified = True

    visualization_script = ""
    visualization_plugins = app_config.visualization_plugins
    current_visualizer_id = workspace_data.get('current_visualizer_id', 'simple_visualizer')
    selected_visualizer = next((p for p in visualization_plugins if p.id() == current_visualizer_id), None)
    if selected_visualizer:
        visualization_script = selected_visualizer.visualize(g_original)
            
    available_workspaces = [(ws_id, data.get('name', ws_id[:8])) for ws_id, data in request.session['workspaces'].items()]

    return render(request, "index.html", {
        "visualization_plugins": visualization_plugins,
        "visualization_script": visualization_script,
        "data_source_plugins": app_config.data_source_plugins,
        "applied_filters": [],
        "current_workspace_id": workspace_id,
        "available_workspaces": available_workspaces,
    }) 


def change_visualization_plugin(request: HttpRequest, workspace_id: str):
    workspace_data = request.session.get('workspaces', {}).get(workspace_id)
    if not workspace_data:
        return redirect('new_workspace') 

    app_config = apps.get_app_config('graph_explorer')
    visualization_plugins = app_config.visualization_plugins
    
    visualization_script = ""
    if request.method == 'GET':
        print(request.GET)
        viz_id = request.GET["id"]
        
        # Update visualizer ID in session
        workspace_data['current_visualizer_id'] = viz_id
        request.session.modified = True
    
        g_filtered = Graph.from_dict(workspace_data['filtered_graph_data'])

        for viz in visualization_plugins:
            if viz.id() == viz_id:
                visualization_script = viz.visualize(g_filtered)
                break

    available_workspaces = [(ws_id, data['name']) for ws_id, data in request.session['workspaces'].items()]

    return render(request, "index.html", {
        "data_source_plugins": app_config.data_source_plugins,
        "visualization_plugins": visualization_plugins,
        "visualization_script": visualization_script,
        "applied_filters": workspace_data['applied_filters'],
        "current_workspace_id": workspace_id,
        "available_workspaces": available_workspaces,
    })

def rename_workspace(request: HttpRequest, workspace_id: str):
    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()

        if 'workspaces' in request.session and workspace_id in request.session['workspaces']:
            if not new_name:
                count = len(request.session['workspaces'])
                new_name = f"Workspace #{count}"
            
            request.session['workspaces'][workspace_id]['name'] = new_name
            request.session.modified = True
            request.session['last_message'] = f"Workspace renamed to '{new_name}'."

    return redirect('index', workspace_id=workspace_id)
