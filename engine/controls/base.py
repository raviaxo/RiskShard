from abc import ABC, abstractmethod
from typing import Dict, Any

class Control(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def apply(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a modified copy of the scenario.
        Must be pure (no mutation).
        """
        pass