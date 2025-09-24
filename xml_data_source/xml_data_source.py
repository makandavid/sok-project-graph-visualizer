import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, date
from typing import Any, Dict, Set

from api.interfaces.data_source_plugin import DataSourcePlugin
from api.models.graph import Graph


INT_RE = re.compile(r"^-?\d+$")
FLOAT_RE = re.compile(r"^-?\d+\.\d+$")


def parse_value(value: str) -> Any:
    """Try to convert a string value into int, float, date or leave as str."""

    if not isinstance(value, str):
        return value

    v = value.strip()
    if v == "":
        return ""

    # Integer
    if INT_RE.match(v):
        try:
            return int(v)
        except Exception:
            pass

    # Float
    if FLOAT_RE.match(v):
        try:
            return float(v)
        except Exception:
            pass

    # Date (ISO)
    try:
        dt = datetime.fromisoformat(v)
        return dt.date()
    except Exception:
        pass

    for fmt in ("%Y-%m-%d", "%d.%m.%Y.", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(v, fmt)
            return dt.date()
        except Exception:
            continue

    # Fallback: string
    return v


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
        id_field: str = kwargs.get("id_field", "id")
        ref_attributes = kwargs.get("ref_attributes", ["ref", "href", "link", "target"]) or []
        max_depth: int = int(kwargs.get("max_depth", 50))
        directed: bool = bool(kwargs.get("directed", True))
        allow_cycles: bool = bool(kwargs.get("allow_cycles", True))

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

        directed_attr = root.attrib.get("directed")
        if directed_attr is not None:
            directed = directed_attr.lower() == "true"

        graph = Graph()

        # Adjacency map for cycle and path existence checks
        adjacency: Dict[str, Set[str]] = {}
        processed_nodes: Set[str] = set()
        counter = 0
        link_counter = 0

        def _ensure_node_in_graph(node_id: str, attributes: Dict[str, Any] | None = None):
            """Add node to graph only once. Create placeholder if attributes is None."""
            if node_id in processed_nodes:
                return

            processed_nodes.add(node_id)

            if attributes is None:
                attributes = {}

            graph.add_node(node_id, attributes)
            adjacency.setdefault(node_id, set())

        def _add_edge(src: str, dst: str) -> bool:
            nonlocal link_counter

            if src not in adjacency:
                adjacency.setdefault(src, set())

                if src not in processed_nodes:
                    graph.add_node(src, {})
                    processed_nodes.add(src)

            if dst not in adjacency:
                adjacency.setdefault(dst, set())

                if dst not in processed_nodes:
                    graph.add_node(dst, {})
                    processed_nodes.add(dst)

            # If cycles are not allowed, check if adding src->dst would create a cycle
            if not allow_cycles:
                # If there already exists a path from dst back to src, then adding src->dst closes a cycle
                if _has_path(dst, src):
                    # Skip adding this edge
                    return False

            # Add directed edge src->dst
            link_counter += 1
            link_id = f"link_{link_counter}_{src}_to_{dst}"
            graph.add_link(link_id, src, dst)
            adjacency[src].add(dst)

            # If undirected, also add the opposite direction
            if not directed:
                link_counter += 1
                back_id = f"link_{link_counter}_{dst}_to_{src}"
                graph.add_link(back_id, dst, src)
                adjacency[dst].add(src)

            return True

        def _has_path(start: str, target: str, visited: Set[str] | None = None) -> bool:
            if visited is None:
                visited = set()

            if start == target:
                return True

            visited.add(start)

            for nb in adjacency.get(start, ()):
                if nb in visited:
                    continue
                if nb == target:
                    return True
                if _has_path(nb, target, visited):
                    return True

            return False

        def get_node_id(elem: ET.Element) -> str:
            nonlocal counter

            if id_field in elem.attrib and elem.attrib[id_field].strip() != "":
                return elem.attrib[id_field]

            counter += 1
            return f"{elem.tag}_{counter}"

        def parse_element(elem: ET.Element, parent_id: str | None = None, depth: int = 0):
            if depth > max_depth:
                return

            node_id = get_node_id(elem)

            # Gather attributes with proper types
            attributes: Dict[str, Any] = {k: parse_value(v) for k, v in elem.attrib.items()}
            # Include text if present
            text_val = (elem.text or "").strip()

            if text_val:
                attributes.setdefault("text", parse_value(text_val))

            # Create node in graph
            _ensure_node_in_graph(node_id, attributes)

            # If parent exists, create a parent->child edge
            if parent_id:
                _add_edge(parent_id, node_id)

            # Handle reference attributes (create edges to referenced ids)
            for k, v in elem.attrib.items():
                if k in ref_attributes:
                    if not v:
                        continue
                    ref_target = v
                    # If reference is a space/comma-separated list, split
                    if "," in ref_target or " " in ref_target:
                        parts = re.split(r"[\s,]+", ref_target.strip())
                        for p in parts:
                            if p:
                                _add_edge(node_id, p)
                    else:
                        _add_edge(node_id, ref_target)

            # Process child elements recursively
            for child in elem:
                parse_element(child, parent_id=node_id, depth=depth + 1)

        # Start parsing from root
        parse_element(root, parent_id=None, depth=0)

        return graph

    def get_supported_extensions(self) -> list[str]:
        return [".xml"]

    def get_required_parameters(self) -> dict:
        return {
            "source": {"type": "string", "description": "Path to XML file or URL", "required": True},
            "id_field": {"type": "string", "description": "XML attribute to use as node ID (default=id)", "required": False},
            "ref_attributes": {"type": "list", "description": "List of attributes treated as references (default=[ref,href,link,target])", "required": False},
            "directed": {"type": "boolean", "description": "Produce a directed graph (default=True)",
                         "required": False},
            "allow_cycles": {"type": "boolean", "description": "Allow cycles in the produced graph (default=True)", "required": False},
            "max_depth": {"type": "integer", "description": "Maximum element nesting depth to parse (default=50)", "required": False},
        }
