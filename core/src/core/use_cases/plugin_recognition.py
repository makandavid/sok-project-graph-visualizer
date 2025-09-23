from importlib.metadata import entry_points
from typing import List

from api.interfaces.data_source_plugin import DataSourcePlugin
from api.interfaces.visualizer_plugin import VisualizerPlugin


class PluginService:
    def __init__(self):
        self.plugins: dict[str, List[DataSourcePlugin | VisualizerPlugin]] = {}

    def load_plugins(self, group: str):
        """
        Dynamically loads plugins based on the entry point group.
        """
        self.plugins[group] = []
        for ep in entry_points(group=group):
            p = ep.load()
            plugin = p()
            self.plugins[group].append(plugin)