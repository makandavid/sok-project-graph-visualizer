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

def filter(g: Graph, attr: str, op: str, val: str) -> Graph:
    if op not in ['==', '<=', '>=', '<', '>', '!=']:
        return g
    if attr is None or attr == "" or val is None or val == "":
        return g
    result = Graph([], [])
    for node in g.nodes:
        if attr not in node.attributes:
            continue

        attr_val = node.attributes[attr]
        value = val
        if not (isinstance(attr_val, float) or isinstance(attr_val, int)):
            attr_val = f"'{str(node.attributes[attr]).lower()}'"
            value = f"'{val.lower()}'"
        
        if eval(f"{str(attr_val)}{op}{value}"):
            result.add_node(node.id, node.attributes)

    for link in g.links:
        result.add_link(link.id, link.source, link.target)
    
    return result