import os
import xml.etree.ElementTree as ET
from api.interfaces.data_source_plugin import DataSourcePlugin
from api.models.graph import Graph

class XmlDataSourcePlugin(DataSourcePlugin):
    """Data source plugin for loading graph data from XML files"""

    def name(self) -> str:
        return "XML Data Source"

    def id(self) -> str:
        return "xml_data_source"

    def load_data(self, source: str, **kwargs) -> Graph:
        """
        Load graph data from any XML file.
        Rules:
        - Each element is a node.
        - Attributes are stored as node properties.
        - Parent-child relationships become edges.
        - Reference attributes create additional edges (support cycles).
        """
        id_field = kwargs.get("id_field", "id")  # XML attribute used as node ID
        ref_attributes = kwargs.get("ref_attributes", ["ref", "href", "link", "target"])
        max_depth = kwargs.get("max_depth", 50)

        # Load XML
        if source.startswith(("http://", "https://")):
            import urllib.request
            with urllib.request.urlopen(source) as response:
                tree = ET.parse(response)
        else:
            if not os.path.exists(source):
                raise FileNotFoundError(f"XML file not found: {source}")
            tree = ET.parse(source)

        root = tree.getroot()
        graph = Graph()
        processed_nodes = {}
        counter = 0  # for generating unique IDs

        def get_node_id(elem):
            nonlocal counter
            if id_field in elem.attrib:
                return elem.attrib[id_field]
            counter += 1
            return f"{elem.tag}_{counter}"

        def parse_element(elem, parent_id=None, depth=0):
            if depth > max_depth:
                return

            node_id = get_node_id(elem)

            if node_id not in processed_nodes:
                # Node attributes
                attributes = {k: v for k, v in elem.attrib.items()}
                if elem.text and elem.text.strip():
                    attributes["text"] = elem.text.strip()

                graph.add_node(node_id, attributes)
                processed_nodes[node_id] = elem

            # Parent → Child edge
            if parent_id:
                link_id = f"{parent_id}_to_{node_id}"
                graph.add_link(link_id, parent_id, node_id)

            # Reference edges (cycle support)
            for k, v in elem.attrib.items():
                if k in ref_attributes:
                    ref_target = v
                    link_id = f"{node_id}_ref_{ref_target}"
                    graph.add_link(link_id, node_id, ref_target)

            # Process child elements recursively
            for child in elem:
                parse_element(child, parent_id=node_id, depth=depth+1)

        parse_element(root)
        return graph

    def get_supported_extensions(self) -> list[str]:
        return [".xml"]

    def get_required_parameters(self) -> dict:
        return {
            "source": {"type": "string", "description": "Path to XML file or URL", "required": True},
            "id_field": {"type": "string", "description": "XML attribute to use as node ID (default=id)", "required": False},
            "ref_attributes": {"type": "list", "description": "List of attributes treated as references (default=[ref,href,link,target])", "required": False}
        }