from api.models.graph import Graph
from django.apps import AppConfig

from core.use_cases.const import VISUALIZER_GROUP, DATASOURCE_GROUP
from core.use_cases.plugin_recognition import PluginService


class GraphExplorerConfig(AppConfig):
    name = 'graph_explorer'
    label = 'graph_explorer'

    plugin_service: PluginService
    current_graph = Graph([], [])
    filtered_graph = Graph([], [])
    applied_filters = []

    def ready(self):
        self.plugin_service = PluginService()
        self.plugin_service.load_plugins(VISUALIZER_GROUP)
        self.plugin_service.load_plugins(DATASOURCE_GROUP)
