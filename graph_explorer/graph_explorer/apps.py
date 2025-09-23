from django.apps import AppConfig
import pkg_resources

from api.models.graph import Graph


class GraphExplorerConfig(AppConfig):
    name = 'graph_explorer'
    label = 'graph_explorer'
    visualization_plugins = []
    current_visualization_plugin = None
    data_source_plugins = []
    current_graph = Graph([], [])
    filtered_graph = Graph([], [])
    applied_filters = []

    def ready(self):
        print("Visualizer plugins:")
        for ep in pkg_resources.iter_entry_points(group='visualizer'):
            p = ep.load()
            print(f"{ep.name} {p}")
            plugin = p()
            self.visualization_plugins.append(plugin)
        
        print("Data source plugins:")
        for ep in pkg_resources.iter_entry_points(group='data_source'):
            p = ep.load()
            print(f"{ep.name} {p}")
            plugin = p()
            self.data_source_plugins.append(plugin)