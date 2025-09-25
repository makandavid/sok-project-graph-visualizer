import json
import os
import tempfile
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.apps import apps
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect

from core.use_cases.const import VISUALIZER_GROUP, DATASOURCE_GROUP
from core.use_cases.cli import handle_command


def get_config():
    """Returns the main app config object."""
    return apps.get_app_config('graph_explorer')


def get_plugins():
    """A helper function to get all plugins."""
    app_config = get_config()
    return app_config.plugin_service.plugins


def get_workspace_service():
    return get_config().workspace_service

def new_workspace(request: HttpRequest):
    """Creates a new workspace with auto-generated name and redirects to it."""
    ws_service = get_workspace_service()
    ws = ws_service.create_workspace()
    return redirect('index', workspace_id=ws.id)


def get_context_data(request: HttpRequest, workspace: 'Workspace'):
    """Prepares the context data for the index.html template."""
    plugins = get_plugins()
    current_visualizer_id = getattr(workspace, 'current_visualizer_id', 'simple_visualizer')
    selected_visualizer = next((p for p in plugins.get(VISUALIZER_GROUP, []) if p.id() == current_visualizer_id), None)
    ws_service = get_workspace_service()
    g_filtered = ws_service.get_graph_from_dict()
    vis_script = selected_visualizer.visualize(g_filtered) if selected_visualizer else ""
    
    plugin_extensions = {p.id(): p.get_supported_extensions() for p in plugins.get(DATASOURCE_GROUP, [])}

    return {
        "visualization_plugins": plugins.get(VISUALIZER_GROUP, []),
        "visualization_script": vis_script,
        "data_source_plugins": plugins.get(DATASOURCE_GROUP, []),
        "plugin_extensions_json": json.dumps(plugin_extensions),
        "selected_data_plugin": getattr(workspace, 'current_data_source_id', None),
        "current_workspace_id": workspace.id,
        "available_workspaces": [(w.id, w.name) for w in get_workspace_service().get_workspaces()],
        "applied_filters": getattr(workspace, 'applied_filters', []),
    }


def index(request: HttpRequest, workspace_id: str = None):
    ws_service = get_workspace_service()
    
    ws = ws_service.select_workspace(workspace_id) if workspace_id else ws_service.get_current_workspace()
    if not ws:
        ws = ws_service.create_workspace()
    
    context = get_context_data(request, ws)
    return render(request, "index.html", context)


@csrf_exempt
def upload_graph(request: HttpRequest, workspace_id: str):
    ws_service = get_workspace_service()
    ws = ws_service.select_workspace(workspace_id)
    if not ws:
        return JsonResponse({"success": False, "error": "Workspace not found."}, status=404)

    if request.method != 'POST':
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

    try:
        upload = request.FILES.get('file') or list(request.FILES.values())[0]
        plugin_id = request.POST.get('plugin_id')
        plugins = get_plugins()
        selected_plugin = next((p for p in plugins.get(DATASOURCE_GROUP, []) if p.id() == plugin_id), None)

        if not selected_plugin:
            raise ValueError(f"Plugin '{plugin_id}' not found")

        ext = os.path.splitext(upload.name)[1] or '.tmp'
        with tempfile.NamedTemporaryFile(mode='wb', suffix=ext, delete=False) as tf:
            for chunk in upload.chunks():
                tf.write(chunk)
            temp_file_path = tf.name

        g = selected_plugin.load_data(temp_file_path)
        ws.graph_data = g.to_dict()
        ws.filtered_graph_data = g.to_dict()
        ws.applied_filters = []
        ws.current_data_source_id = plugin_id

        vis_script = get_context_data(request, ws)['visualization_script']

        return JsonResponse({
            "success": True,
            "visualization_script": vis_script,
            "node_count": len(g.nodes),
            "link_count": len(g.links)
        })
    
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def search_filter(request: HttpRequest, workspace_id: str):
    ws_service = get_workspace_service()
    ws = ws_service.select_workspace(workspace_id)
    if not ws:
        ws = ws_service.create_workspace()

    g = ws_service.get_graph_from_dict()
    filter_str = ""
    error_message = None

    try:
        if "search" in request.GET:
            filter_str = request.GET["search"]
            ws_service.search_graph(filter_str)
        else:
            attr = request.GET["attr"]
            op = request.GET["op"] 
            val = request.GET["val"]
            ws_service.filter_graph(attr, op, val)
    except Exception as e:
        error_message = f"Filter error: {e}"

    context = get_context_data(request, ws)
    context['error_message'] = error_message
    return render(request, "index.html", context)


def reset_filter(request: HttpRequest, workspace_id: str):
    ws_service = get_workspace_service()
    ws = ws_service.select_workspace(workspace_id)
    if not ws:
        return redirect('index')

    ws.filtered_graph_data = ws.graph_data
    ws.applied_filters = []

    context = get_context_data(request, ws)
    return render(request, "index.html", context)


def change_visualization_plugin(request: HttpRequest, workspace_id: str):
    ws_service = get_workspace_service()
    ws = ws_service.select_workspace(workspace_id)
    if not ws:
        return redirect('index')

    if request.method == 'GET':
        viz_id = request.GET.get("id")
        if viz_id:
            ws.current_visualizer_id = viz_id

    context = get_context_data(request, ws)
    return render(request, "index.html", context)


@csrf_exempt
def cli_execute(request: HttpRequest, workspace_id: str):
    ws_service = get_workspace_service()
    ws = ws_service.select_workspace(workspace_id)
    if not ws:
        return JsonResponse({"success": False, "error": "Workspace not found."}, status=404)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

    data = json.loads(request.body)
    command_str = data.get("command", "")
    
    g = ws_service.get_graph_from_dict()
    
    try:
        result = handle_command(g, command_str)
        ws.filtered_graph_data = g.to_dict()

        vis_script = get_context_data(request, ws)['visualization_script']

        return JsonResponse({
            "success": True,
            "result": result,
            "visualization_script": vis_script
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def rename_workspace(request: HttpRequest, workspace_id: str):
    if request.method != 'POST':
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

    ws_service = get_workspace_service()

    new_name = request.POST.get('name', '').strip()
    if not new_name:
        ws = ws_service.select_workspace(workspace_id)
        if not ws:
            return JsonResponse({"success": False, "error": "Workspace not found."}, status=404)
        count = len(ws_service.get_workspaces())
        new_name = f"Workspace #{count}"

    success = ws_service.rename_workspace(workspace_id, new_name)
    if not success:
        return JsonResponse({"success": False, "error": "Workspace not found."}, status=404)

    return redirect('index', workspace_id=workspace_id)

