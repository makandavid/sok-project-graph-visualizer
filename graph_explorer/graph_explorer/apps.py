from django.apps import AppConfig
import pkg_resources

from api.models.graph import Graph


class GraphExplorerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'graph_explorer'
    label = 'graph_explorer'
    visualization_plugins = []
    current_graph = Graph([], [])

    def ready(self):
        print("Visualizer plugins:")
        for ep in pkg_resources.iter_entry_points(group='visualizer'):
            p = ep.load()
            print("{} {}".format(ep.name, p))
            plugin = p()
            self.visualization_plugins.append(plugin)