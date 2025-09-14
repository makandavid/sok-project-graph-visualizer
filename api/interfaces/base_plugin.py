from abc import ABC, abstractmethod

class BasePlugin(ABC):

    @abstractmethod
    def name(self) -> str:
        """Return the name of the plugin"""
        pass

    @abstractmethod
    def id(self) -> str:
        """Return the unique identifier of the plugin"""
        pass
    