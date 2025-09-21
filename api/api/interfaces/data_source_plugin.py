from abc import abstractmethod
from ..models.graph import Graph
from .base_plugin import BasePlugin


class DataSourcePlugin(BasePlugin):
    """Base class for data source plugins that load graph data from various sources"""
    
    @abstractmethod
    def load_data(self, source: str) -> Graph:
        """Load graph data from the specified source
        
        Args:
            source: The data source (file path, URL, etc.)
            
        Returns:
            Graph: The loaded graph data
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """Return list of supported file extensions or source types
        
        Returns:
            list[str]: List of supported extensions (e.g., ['.json', '.csv'])
        """
        raise NotImplementedError
