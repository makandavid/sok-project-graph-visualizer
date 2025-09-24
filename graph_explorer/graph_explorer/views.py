import json
import os
import tempfile
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.apps import apps
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect

from api.models.graph import Graph
from api.services.search_filter import search, filter
from core.use_cases.const import VISUALIZER_GROUP, DATASOURCE_GROUP
from .cli import handle_command


def get_config():
    """Returns the main app config object."""
    return apps.get_app_config('graph_explorer')


def get_plugins():
    """A helper function to get all plugins."""
    app_config = get_config()
    return app_config.plugin_service.plugins


def get_workspace(request: HttpRequest, workspace_id: str):
    """Retrieves a workspace or returns None if not found."""
    workspace_data = request.session.get('workspaces', {}).get(workspace_id)
    if not workspace_data:
        return None  

    return workspace_data

def new_workspace(request: HttpRequest):
    """Creates a new workspace with auto-generated name and redirects to it."""
    workspace_id = str(uuid.uuid4())
    return redirect('index', workspace_id=workspace_id)


def get_available_workspaces(session):
    """Returns a list of available workspaces for the template."""
    return [(ws_id, data.get('name', ws_id[:8])) for ws_id, data in session.get('workspaces', {}).items()]


def get_context_data(request: HttpRequest, workspace_data):
    """Prepares the context data for the index.html template."""
    app_config = get_config()
    plugins = get_plugins()
    
    current_visualizer_id = workspace_data.get('current_visualizer_id', 'simple_visualizer')
    selected_visualizer = next((p for p in plugins.get(VISUALIZER_GROUP, []) if p.id() == current_visualizer_id), None)
    
    g_filtered = Graph.from_dict(workspace_data['filtered_graph_data'])
    vis_script = selected_visualizer.visualize(g_filtered) if selected_visualizer else ""

    plugin_extensions = json.loads(workspace_data.get('plugin_extensions_json', '{}'))

    return {
        "visualization_plugins": plugins.get(VISUALIZER_GROUP, []),
        "visualization_script": vis_script,
        "data_source_plugins": plugins.get(DATASOURCE_GROUP, []),
        "plugin_extensions_json": json.dumps(plugin_extensions),
        "selected_data_plugin": workspace_data.get('current_data_source_id'),
        "current_workspace_id": request.resolver_match.kwargs.get('workspace_id'),
        "available_workspaces": get_available_workspaces(request.session),
        "applied_filters": workspace_data.get('applied_filters', []),
    }


def index(request: HttpRequest, workspace_id: str):
    app_config = get_config()
    plugins = get_plugins()
    session_workspaces = request.session.setdefault('workspaces', {})
    workspace_data = session_workspaces.get(workspace_id)
    
    if not workspace_data:
        print(f"Radni prostor '{workspace_id}' ne postoji. Kreiram ga.")
        data_source_id = request.GET.get('source', 'json_data_source')
        selected_data_plugin = next((p for p in plugins.get(DATASOURCE_GROUP, []) if p.id() == data_source_id), None)
        selected_visualizer_id = next((p.id() for p in plugins.get(VISUALIZER_GROUP, []) if p.id() == 'simple_visualizer'), None)
        
        if not selected_data_plugin and plugins.get(DATASOURCE_GROUP):
            selected_data_plugin = plugins[DATASOURCE_GROUP][0]
        
        plugin_extensions = {p.id(): p.get_supported_extensions() for p in plugins.get(DATASOURCE_GROUP, [])}
        g = create_fallback_graph()
        
        request.session['workspaces'][workspace_id] = {
            'name': f"Workspace #{len(session_workspaces) + 1}",
            'graph_data': g.to_dict(),
            'filtered_graph_data': g.to_dict(),
            'applied_filters': [],
            'current_data_source_id': selected_data_plugin.id() if selected_data_plugin else None,
            'current_visualizer_id': selected_visualizer_id,
            'plugin_extensions_json': json.dumps(plugin_extensions),
        }
        request.session.modified = True
        workspace_data = request.session['workspaces'][workspace_id]
        print(f"Workspace '{workspace_id}' saved.")
    
    context = get_context_data(request, workspace_data)
    print(f"Number of nodes in the filtered graph: {len(Graph.from_dict(workspace_data['filtered_graph_data']).nodes)}")
    
    return render(request, "index.html", context)


@csrf_exempt
def upload_graph(request: HttpRequest, workspace_id: str):
    workspace_data = get_workspace(request, workspace_id)
    if not workspace_data:
        return JsonResponse({"success": False, "error": "Workspace not found."}, status=404)

    if request.method != 'POST':
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

    temp_file_path = None
    try:
        if not request.FILES:
            raise ValueError("No file uploaded")
        
        upload = request.FILES.get('file') or list(request.FILES.values())[0]
        plugin_id = request.POST.get('plugin_id')
        if not plugin_id:
            raise ValueError("Missing plugin_id")
        
        plugins = get_plugins()
        selected_plugin = next((p for p in plugins.get(DATASOURCE_GROUP, []) if p.id() == plugin_id), None)
        if not selected_plugin:
            raise ValueError(f"Data source plugin '{plugin_id}' not found")
        
        ext = os.path.splitext(upload.name)[1] or '.tmp'
        with tempfile.NamedTemporaryFile(mode='wb', suffix=ext, delete=False) as tf:
            for chunk in upload.chunks():
                tf.write(chunk)
            temp_file_path = tf.name

        graph = selected_plugin.load_data(temp_file_path)
        print("Total nodes:", len(graph.nodes), " Total links:", len(graph.links))

        workspace_data['graph_data'] = graph.to_dict()
        workspace_data['filtered_graph_data'] = graph.to_dict()
        workspace_data['applied_filters'] = []
        workspace_data['current_data_source_id'] = plugin_id
        request.session.modified = True

        vis_script = get_visualizer_script(workspace_data, graph)

        return JsonResponse({
            "success": True,
            "visualization_script": vis_script,
            "node_count": len(graph.nodes),
            "link_count": len(graph.links)
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def get_visualizer_script(workspace_data, graph_obj):
    """Helper function to get the visualizer script."""
    plugins = get_plugins()
    current_visualizer_id = workspace_data.get('current_visualizer_id', 'simple_visualizer')
    selected_visualizer = next((p for p in plugins.get(VISUALIZER_GROUP, []) if p.id() == current_visualizer_id), None)
    return selected_visualizer.visualize(graph_obj) if selected_visualizer else ""


@csrf_exempt
def cli_execute(request: HttpRequest, workspace_id: str):
    workspace_data = get_workspace(request, workspace_id)
    if not workspace_data:
        return JsonResponse({"success": False, "error": "Workspace not found."}, status=404)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

    data = json.loads(request.body)
    command_str = data.get("command", "")
    
    g = Graph.from_dict(workspace_data['filtered_graph_data'])
    
    try:
        result = handle_command(g, command_str)
        
        workspace_data['filtered_graph_data'] = g.to_dict()
        request.session.modified = True

        vis_script = get_visualizer_script(workspace_data, g)

        return JsonResponse({
            "success": True,
            "result": result,
            "visualization_script": vis_script
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
    

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
    workspace_data = get_workspace(request, workspace_id)
    if not workspace_data:
        return redirect('new_workspace')

    g = Graph.from_dict(workspace_data['filtered_graph_data'])
    filter_str = ""
    error_message = None

    if request.method == 'GET':
        try:
            if "search" in request.GET:
                g = search(g, request.GET["search"])
                filter_str = request.GET["search"]
            else:
                ops = {'eq': '==', 'le': '<=', 'ge': '>=', 'lt': '<', 'gt': '>', 'ne': '!='}
                g = filter(g, request.GET["attr"], ops[request.GET["op"]], request.GET["val"])
                filter_str = f"{request.GET['attr']} {ops[request.GET['op']]} {request.GET['val']}"

            workspace_data['filtered_graph_data'] = g.to_dict()
            workspace_data['applied_filters'].append(filter_str)
            request.session.modified = True
            
        except Exception as e:
            error_message = "Filter error: Can't compare different types!"
            print(f"Filter error details: {e}")
            
    context = get_context_data(request, workspace_data)
    context['error_message'] = error_message
    
    return render(request, "index.html", context) 


def reset_filter(request: HttpRequest, workspace_id: str):
    workspace_data = get_workspace(request, workspace_id)
    if not workspace_data:
        return redirect('new_workspace')

    g_original = Graph.from_dict(workspace_data['graph_data'])
    workspace_data['filtered_graph_data'] = g_original.to_dict()
    workspace_data['applied_filters'] = []
    request.session.modified = True
    
    context = get_context_data(request, workspace_data)
    
    return render(request, "index.html", context) 


def change_visualization_plugin(request: HttpRequest, workspace_id: str):
    workspace_data = get_workspace(request, workspace_id)
    if not workspace_data:
        return redirect('new_workspace')

    if request.method == 'GET':
        viz_id = request.GET.get("id")
        if not viz_id:
            return JsonResponse({"success": False, "error": "Missing visualizer ID."}, status=400)
            
        workspace_data['current_visualizer_id'] = viz_id
        request.session.modified = True
        
    context = get_context_data(request, workspace_data)
    return render(request, "index.html", context)


def rename_workspace(request: HttpRequest, workspace_id: str):
    if request.method != 'POST':
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

    workspace_data = get_workspace(request, workspace_id)
    if not workspace_data:
        return JsonResponse({"success": False, "error": "Workspace not found."}, status=404)

    new_name = request.POST.get('name', '').strip()
    if not new_name:
        count = len(request.session['workspaces'])
        new_name = f"Workspace #{count}"
        
    workspace_data['name'] = new_name
    request.session.modified = True
    request.session['last_message'] = f"Workspace renamed to '{new_name}'."
    
    return redirect('index', workspace_id=workspace_id)