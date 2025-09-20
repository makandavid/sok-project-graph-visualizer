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

def index(request: HttpRequest):
    app_config = apps.get_app_config('graph_explorer')
    visualization_plugins = app_config.visualization_plugins
    data_source_plugins = app_config.data_source_plugins
    
    # Initialize graph
    g = Graph([], [])
    json_data_source = None
    
    # Find JSON data source plugin
    for plugin in data_source_plugins:
        if plugin.id() == "json_data_source":
            json_data_source = plugin
            break
    
    # Handle file upload
    if request.method == 'POST' and 'json_file' in request.FILES:
        uploaded_file = request.FILES['json_file']
        
        # Validate file type
        if not uploaded_file.name.lower().endswith('.json'):
            return redirect('index')
        
        try:
            # Read and parse the uploaded JSON file
            file_content = uploaded_file.read().decode('utf-8')
            json_data = json.loads(file_content)
            
            # Save the uploaded file temporarily or permanently
            # Option 1: Use temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            if json_data_source:
                try:
                    # Load data using the JSON data source plugin
                    g = json_data_source.load_data(temp_file_path)
                    print(request, f'Successfully loaded graph with {len(g.nodes)} nodes and {len(g.links)} links from {uploaded_file.name}')
                    
                    # Clean up temporary file
                    os.unlink(temp_file_path)
                    
                except Exception as e:
                    messages.error(request, f'Error parsing graph data: {str(e)}')
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                    g = create_fallback_graph()
            else:
                messages.error(request, 'JSON data source plugin not available')
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                g = create_fallback_graph()
                
        except json.JSONDecodeError as e:
            messages.error(request, f'Invalid JSON format: {str(e)}')
            g = create_fallback_graph()
        except UnicodeDecodeError as e:
            messages.error(request, f'File encoding error: {str(e)}')
            g = create_fallback_graph()
        except Exception as e:
            messages.error(request, f'Unexpected error: {str(e)}')
            g = create_fallback_graph()
    
    # Handle GET request or fallback after failed upload
    else:
        print("Went into this shit")
        if json_data_source:
            try:
                # Try to load data from default sample JSON file
                g = json_data_source.load_data("../json_data_source/data/test.json")
                print(f"Loaded graph with {len(g.nodes)} nodes and {len(g.links)} links")
            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                print(f"Error loading JSON data: {e}")
                # Fallback to hardcoded data
                g = create_fallback_graph()
        else:
            print("No JSON data source plugin found, using fallback data")
            g = create_fallback_graph()
    
    # Store current graph in app config
    app_config.current_graph = g
    
    # Generate visualization script
    if visualization_plugins:
        visualization_script = visualization_plugins[0].visualize(g)
    else:
        visualization_script = ""
    
    return render(request, "index.html", {
        "visualization_plugins": visualization_plugins,
        "visualization_script": visualization_script
    })
    

@csrf_exempt
def upload_graph(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            json_data = data.get('json_data')
            filename = data.get('filename', 'uploaded.json')
            
            # Save temporarily
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_file.write(json.dumps(json_data))
                temp_file_path = temp_file.name
            
            # Load using JSON data source
            app_config = apps.get_app_config('graph_explorer')
            json_data_source = None
            for plugin in app_config.data_source_plugins:
                if plugin.id() == "json_data_source":
                    json_data_source = plugin
                    break

            if json_data_source:
                g = json_data_source.load_data(temp_file_path)
                app_config.current_graph = g

                # Generate visualization script
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
