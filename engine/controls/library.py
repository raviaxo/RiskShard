from copy import deepcopy
from .base import Control

class FrequencyReduction(Control):
    def __init__(self, reduction_pct: float):
        super().__init__("frequency_reduction")
        self.reduction_pct = reduction_pct

    def apply(self, scenario):
        s = deepcopy(scenario)
        s["frequency"]["mean"] *= (1 - self.reduction_pct)
        return s


class ImpactReduction(Control):
    def __init__(self, reduction_pct: float):
        super().__init__("impact_reduction")
        self.reduction_pct = reduction_pct

    def apply(self, scenario):
        s = deepcopy(scenario)
        s["impact"]["mode"] *= (1 - self.reduction_pct)
        s["impact"]["max"] *= (1 - self.reduction_pct)
        return s