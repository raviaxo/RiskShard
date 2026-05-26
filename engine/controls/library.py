from copy import deepcopy
from .base import Control


def scale_range(values, reduction_pct):
    multiplier = 1 - reduction_pct
    return {
        "min": values["min"] * multiplier,
        "likely": values["likely"] * multiplier,
        "max": values["max"] * multiplier,
    }


class FrequencyReduction(Control):
    def __init__(self, reduction_pct: float):
        super().__init__("frequency_reduction")
        self.reduction_pct = reduction_pct

    def apply(self, scenario):
        s = deepcopy(scenario)
        s["frequency"] = scale_range(s["frequency"], self.reduction_pct)
        return s


class ImpactReduction(Control):
    def __init__(self, reduction_pct: float):
        super().__init__("impact_reduction")
        self.reduction_pct = reduction_pct

    def apply(self, scenario):
        s = deepcopy(scenario)
        s["impact"] = scale_range(s["impact"], self.reduction_pct)
        return s
