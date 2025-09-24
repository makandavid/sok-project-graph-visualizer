import uuid
from typing import List
from api.models.graph import Graph


class Workspace:
    def __init__(self, id: str = None, name: str = None, graph: Graph = None):
        self.id = id or str(uuid.uuid4())
        self.name = name or f"Workspace-{self.id[:8]}"
        self.graph_data = graph.to_dict() if graph else None
        self.filtered_graph_data = graph.to_dict() if graph else None
        self.applied_filters: List[str] = []
        self.current_data_source_id: str = None
        self.current_visualizer_id: str = "simple_visualizer"
        self.plugin_extensions_json: str = "{}"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "graph_data": self.graph_data,
            "filtered_graph_data": self.filtered_graph_data,
            "applied_filters": self.applied_filters,
            "current_data_source_id": self.current_data_source_id,
            "current_visualizer_id": self.current_visualizer_id,
            "plugin_extensions_json": self.plugin_extensions_json,
        }

    @classmethod
    def from_dict(cls, data: dict):
        ws = cls(id=data.get("id"), name=data.get("name"))
        ws.graph_data = data.get("graph_data")
        ws.filtered_graph_data = data.get("filtered_graph_data")
        ws.applied_filters = data.get("applied_filters", [])
        ws.current_data_source_id = data.get("current_data_source_id")
        ws.current_visualizer_id = data.get("current_visualizer_id", "simple_visualizer")
        ws.plugin_extensions_json = data.get("plugin_extensions_json", "{}")
        return ws
