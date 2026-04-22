from typing import List, Dict, Any
from .base import Control

def apply_controls(
    scenario: Dict[str, Any],
    controls: List[Control]
) -> Dict[str, Any]:
    modified = scenario
    for control in controls:
        modified = control.apply(modified)
    return modified