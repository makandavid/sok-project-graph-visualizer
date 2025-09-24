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