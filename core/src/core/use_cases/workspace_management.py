from typing import List, Optional
from api.models.graph import Graph
from api.models.workspace import Workspace
from api.services.search_filter import search, filter

class WorkspaceService:
    def __init__(self):
        self.workspaces: List[Workspace] = []
        self.current_workspace: Optional[Workspace] = None

    def create_workspace(self, graph: Optional[Graph] = None, name: Optional[str] = None) -> Workspace:
        if graph is None:
            graph = self.create_fallback_graph()
        if name is None:
            name = f"Workspace #{len(self.workspaces) + 1}"
        ws = Workspace(graph=graph, name=name)
        self.workspaces.append(ws)
        self.current_workspace = ws
        return ws

    def get_current_workspace(self) -> Optional[Workspace]:
        return self.current_workspace

    def select_workspace(self, workspace_id: str) -> Optional[Workspace]:
        ws = next((w for w in self.workspaces if w.id == workspace_id), None)
        if ws:
            self.current_workspace = ws
        return ws

    def get_workspaces(self) -> List[Workspace]:
        return self.workspaces

    def rename_workspace(self, workspace_id: str, new_name: str) -> bool:
        ws = next((w for w in self.workspaces if w.id == workspace_id), None)
        if not ws:
            return False
        ws.name = new_name
        return True

    def get_graph_from_dict(self) -> Graph:
        return Graph.from_dict(self.current_workspace.filtered_graph_data)
    

    def search_graph(self, query: str) -> Graph:
        g = self.get_graph_from_dict()
        g = search(g, query)
        self.current_workspace.filtered_graph_data = g.to_dict()
        self.current_workspace.applied_filters.append(query)
        return g

    def filter_graph(self, attr: str, op: str, val: str) -> Graph:
        g = self.get_graph_from_dict()
        ops = {'eq': '==', 'le': '<=', 'ge': '>=', 'lt': '<', 'gt': '>', 'ne': '!='}
        if op not in ops:
            raise ValueError(f"Unknown operator: {op}")
        g = filter(g, attr, ops[op], val)
        filter_str = f"{attr} {ops[op]} {val}"
        self.current_workspace.filtered_graph_data = g.to_dict()
        self.current_workspace.applied_filters.append(filter_str)
        return g

    
    def create_fallback_graph(self) -> Graph:
        g = Graph([], [])
        g.add_node("0", {'a': 23, 'b': 56})
        g.add_node("1", {'a': 65, 'b': 47})
        g.add_node("2", {'a': 54, 'b': 45})
        g.add_node("3", {'a': 21, 'b': 21})
        g.add_node("4", {'a': 69, 'b': 56})
        g.add_node("5", {'a': 99, 'b': 96, 'c': 23})
        g.add_node("6", {'a': 100, 'b': 56, 'c': 200, 'd': 300, 'e': 267})
        g.add_node("7", {'a': 3})
        g.add_link("0", "1", "2")
        g.add_link("1", "1", "4")
        g.add_link("2", "1", "3")
        g.add_link("3", "2", "4")
        g.add_link("4", "3", "2")
        g.add_link("5", "3", "6")
        g.add_link("6", "3", "5")
        g.add_link("7", "4", "0")
        return g