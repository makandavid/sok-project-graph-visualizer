from api.models.graph import Graph


def search(g: Graph, text: str) -> Graph:
    if text is None or text == "":
        return g
    result = Graph()
    for node in g.nodes:
        if text.lower() in str(node.id).lower():
            result.add_node(node.id, node.attributes)
            continue
        for val in node.attributes.values():
            if text.lower() in str(val).lower():
                result.add_node(node.id, node.attributes)
                break
    for link in g.links:
        result.add_link(link.id, link.source, link.target)
    
    return result