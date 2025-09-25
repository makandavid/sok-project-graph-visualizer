from django.apps import AppConfig

from core.use_cases.const import VISUALIZER_GROUP, DATASOURCE_GROUP
from core.use_cases.plugin_recognition import PluginService
from core.use_cases.workspace_management import WorkspaceService


class GraphExplorerConfig(AppConfig):
    name = 'graph_explorer'
    label = 'graph_explorer'

    plugin_service: PluginService
    workspace_service: WorkspaceService

    def ready(self):
        self.plugin_service = PluginService()
        self.workspace_service = WorkspaceService()
        self.plugin_service.load_plugins(VISUALIZER_GROUP)
        self.plugin_service.load_plugins(DATASOURCE_GROUP)
