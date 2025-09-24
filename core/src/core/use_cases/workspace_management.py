from typing import List, Optional
from api.models.graph import Graph
from api.models.workspace import Workspace

class WorkspaceService:
    def __init__(self):
        self.workspaces: List[Workspace] = []
        self.current_workspace: Optional[Workspace] = None

    def create_workspace(self, graph: Optional[Graph] = None, name: Optional[str] = None) -> Workspace:
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