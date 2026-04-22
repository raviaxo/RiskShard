def simulate_with_controls(
    scenario: dict,
    controls: list,
    simulate_fn
):
    # Baseline
    baseline_results = simulate_fn(scenario)

    # Apply controls
    modified_scenario = apply_controls(scenario, controls)

    # Re-run
    controlled_results = simulate_fn(modified_scenario)

    # Compare
    comparison = compare_runs(baseline_results, controlled_results)

    return {
        "baseline": baseline_results,
        "controlled": controlled_results,
        "comparison": comparison
    }de