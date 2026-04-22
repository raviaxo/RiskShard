def compare_runs(before: dict, after: dict) -> dict:
    def delta(a, b):
        return b - a

    return {
        "mean_delta": delta(before["mean"], after["mean"]),
        "p95_delta": delta(before["p95"], after["p95"]),
        "p99_delta": delta(before["p99"], after["p99"]),
        "reduction_pct_p95": (before["p95"] - after["p95"]) / before["p95"]
    }