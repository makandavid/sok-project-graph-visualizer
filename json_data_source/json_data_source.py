import json
import os
import urllib.request
import urllib.parse
from api.interfaces.data_source_plugin import DataSourcePlugin
from api.models.graph import Graph
from dateutil import parser as dateparser


class JsonDataSourcePlugin(DataSourcePlugin):
    """Data source plugin for loading graph data from JSON files with hierarchical structure"""
    
    def name(self) -> str:
        return "JSON Data Source"
    
    def id(self) -> str:
        return "json_data_source"
    
    def load_data(self, source: str, **kwargs) -> Graph:
        """Load graph data from a JSON file with hierarchical structure
        
        Expected JSON format:
        {
            "@id": "28dddab1-4aa7-6e2b-b0b2-7ed9096aa9bc",
            "name": "I'm parent",
            "children": [
                {
                    "@id": "6616c598-0a0a-8263-7a56-fb0c0e16225a",
                    "name": "I'm first child",
                    "parent": "28dddab1-4aa7-6e2b-b0b2-7ed9096aa9bc"
                }
            ]
        }
        
        Parameters:
        - id_field: Field name for node ID (default: "@id")
        - children_field: Field name for children array (default: "children")
        - parent_field: Field name for parent reference (default: "parent")
        - max_depth: Maximum parsing depth (default: 10)
        """
        # Parse parameters
        id_field = kwargs.get('id_field', '@id')
        children_field = kwargs.get('children_field', 'children')
        parent_field = kwargs.get('parent_field', 'parent')
        max_depth = kwargs.get('max_depth', 10)
        
        # Load JSON data
        if source.startswith(('http://', 'https://')):
            try:
                with urllib.request.urlopen(source) as response:
                    data = json.loads(response.read().decode('utf-8'))
            except Exception as e:
                raise Exception(f"Failed to load JSON from URL {source}: {e}")
        else:
            if not os.path.exists(source):
                raise FileNotFoundError(f"JSON file not found: {source}")
            
            with open(source, 'r', encoding='utf-8') as file:
                data = json.load(file)
        
        graph = Graph()
        processed_nodes = set()  # Track processed nodes to avoid infinite loops
        
        def parse_node(node_data, depth=0, parent_id=None):
            """Recursively parse a node and its children"""
            if depth > max_depth:
                return
            
            # Extract node ID
            node_id = str(node_data.get(id_field))
            if not node_id:
                return
            
            # Skip if already processed (avoid infinite loops in cyclic graphs)
            if node_id in processed_nodes:
                return
            
            processed_nodes.add(node_id)
            
            # Extract attributes (all fields except special ones)
            attributes = {}
            for key, value in node_data.items():
                if key not in [id_field, children_field, parent_field]:
                    if isinstance(value, str):
                        try:
                            value = dateparser.parse(value)
                        except (ValueError, OverflowError):
                            pass
                    attributes[key] = value
            
            # Add node to graph
            graph.add_node(node_id, attributes)
            
            # Create parent-child link if parent_id is provided
            if parent_id:
                link_id = f"{parent_id}_to_{node_id}"
                graph.add_link(link_id, parent_id, node_id)
            
            # Process children
            children = node_data.get(children_field, [])
            if isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
                        parse_node(child, depth + 1, node_id)
            
            # Process parent reference if it exists
            parent_ref = node_data.get(parent_field)
            if parent_ref and parent_ref != parent_id:
                # Create link from child to parent
                link_id = f"{node_id}_to_{parent_ref}"
                graph.add_link(link_id, node_id, parent_ref)
        
        # Start parsing from root
        if isinstance(data, dict):
            parse_node(data)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    parse_node(item)
        
        return graph
    
    def get_supported_extensions(self) -> list[str]:
        return ['.json']
    
    def get_required_parameters(self) -> dict:
        """Return required parameters for this data source"""
        return {
            'source': {
                'type': 'string',
                'description': 'Path to JSON file or URL',
                'required': True
            },
            'id_field': {
                'type': 'string',
                'description': 'Field name for node ID',
                'default': '@id',
                'required': False
            },
            'children_field': {
                'type': 'string',
                'description': 'Field name for children array',
                'default': 'children',
                'required': False
            },
            'parent_field': {
                'type': 'string',
                'description': 'Field name for parent reference',
                'default': 'parent',
                'required': False
            },
            'max_depth': {
                'type': 'integer',
                'description': 'Maximum parsing depth',
                'default': 10,
                'required': False
            }
        }
