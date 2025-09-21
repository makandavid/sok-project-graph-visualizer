import shlex
from api.services.search_filter import search, filter


def handle_command(graph, command_str: str):
    tokens = shlex.split(command_str)
    if not tokens:
        return "No command entered"

    cmd = tokens[0]

    if cmd == "create":
        return handle_create(graph, tokens[1:])
    elif cmd == "edit":
        return handle_edit(graph, tokens[1:])
    elif cmd == "delete":
        return handle_delete(graph, tokens[1:])
    elif cmd == "filter":
        return handle_filter(graph, " ".join(tokens[1:]))
    elif cmd == "search":
        return handle_search(graph, " ".join(tokens[1:]))
    elif cmd == "clear":
        graph.nodes = []
        graph.links = []
        return "Graph cleared"
    else:
        return f"Unknown command: {cmd}"


def handle_create(graph, args):
    if args[0] == "node":
        node_id = None
        attributes = {}
        for arg in args[1:]:
            if arg.startswith("--id="):
                node_id = arg.split("=", 1)[1]
            elif arg.startswith("--property="):
                try:
                    key, val = arg.split("=", 1)[1].split("=", 1)
                    attributes[key] = val
                except ValueError:
                    raise ValueError(f"Invalid property format: {arg}. Use --property=Key=Value")
        if node_id is None:
            raise ValueError("Node requires --id")
        print(graph.add_node(node_id, attributes))
        return f"Node {node_id} created with {attributes}"

    elif args[0] == "edge":
        edge_id = None
        properties = {}
        node_ids = []
        for arg in args[1:]:
            if arg.startswith("--id="):
                edge_id = arg.split("=", 1)[1]
            elif arg.startswith("--property="):
                try:
                    key, val = arg.split("=", 1)[1].split("=", 1)
                    properties[key] = val
                except ValueError:
                    raise ValueError(f"Invalid property format: {arg}. Use --property=Key=Value")
            else:
                node_ids.append(int(arg))
        if len(node_ids) != 2:
            raise ValueError("Edge requires source and target node IDs")
        for n in graph.nodes:
            print(type(n.id))
        print(graph.add_link(edge_id, str(node_ids[0]), str(node_ids[1])))
        return f"Edge {edge_id} created between {node_ids} with {properties}"

def handle_edit(graph, args):
    if args[0] == "node":
        node_id = args[1].split("=")[1]  # --id=2
        node = next((n for n in graph.nodes if n.id == node_id), None)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        for arg in args[2:]:
            if arg.startswith("--property"):
                key, val = arg.split("=", 1)[1].split("=")
                node.attributes[key] = val
        return f"Node {node_id} updated to {node.attributes}"


def handle_delete(graph, args):
    if args[0] == "node":
        node_id = args[1].split("=")[1]
        # Ensure no edges use this node
        for link in graph.links:
            if link.source == node_id or link.target == node_id:
                raise ValueError(f"Cannot delete node {node_id}, it still has edges")
        graph.nodes = [n for n in graph.nodes if n.id != node_id]
        return f"Node {node_id} deleted"
    elif args[0] == "edge":
        edge_id = args[1].split("=")[1]
        for l in graph.links:
            print(l.id)
        graph.links = [e for e in graph.links if e.id != edge_id]
        return f"Edge {edge_id} deleted"


def handle_search(graph, expr: str):
    # expr is the text to search for
    new_graph = search(graph, expr)
    graph.nodes = new_graph.nodes
    graph.links = new_graph.links
    return f"Searched for: {expr}"

def handle_filter(graph, expr: str):
    # expr example: "Age>=30" or "Height<150"
    import re
    match = re.match(r"(\w+)\s*(==|!=|<=|>=|<|>)\s*(.+)", expr)
    if not match:
        return f"Invalid filter expression: {expr}"
    attr, op, val = match.groups()
    new_graph = filter(graph, attr, op, val)
    graph.nodes = new_graph.nodes
    graph.links = new_graph.links
    return f"Applied filter: {expr}"