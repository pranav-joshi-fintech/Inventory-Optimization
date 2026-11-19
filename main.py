# main.py
"""
Contributor(s): Pranav Joshi
Project Name: Inventory Optimization

RUN THIS FILE TO EXECUTE THE PROJECT.
Please refer to the README.md file for more information on the project.
"""

# *** IMPORTS ***
import random
# Uses Wagner-Whitin algorithm to solve the lot-sizing problem
from improved_strategy import PlanningData, build_and_solve
# Uses a more traditional "lot-for-lot" approach to solve the lot-sizing problem
# (a.k.a, they just buy what they need, as required with some comfortable surplus inventory)
from baseline_strategy import lot_for_lot


# *** CONFIG ***
config = {
    # if True, run 999 random scenarios to test the optimizer. Else, just run the default scenario.
    "test_consistency": True,
    # if True, print the report for each scenario (only if test_consistency is also True).
    "report_results": True,
    # if None, use the default scenario. Else, use this seed to generate a random scenario.
    "test_seed": None,
}



# *** FUNCTIONS ***
"""
Check "planning_data.py" for the definitions of PlanningData and Plan.

A "Nat" is an Int that is >=1.
"""


# Using the random library, generate a random scenario with demand for each day.
# make_scenario: Nat Nat -> PlanningData
def make_scenario(weeks=12, seed=7) -> PlanningData:
    """
    A default 12-week scenario with seasonal demand and a meaningful setup cost,
    so batching (and therefore optimization) clearly pays off.
    """
    rng = random.Random(seed)
    demand = [round(100 + 60 * abs((t % 6) - 3) + rng.uniform(-15, 15)) for t in range(weeks)]
    prod_cost = [2.0] * weeks
    hold_cost = [0.5] * weeks # it's cheap to hold inventory
    setup_cost = [400.0] * weeks # but expensive to order a new batch
    capacity = [1000.0] * weeks  # plenty of capacity means batching is viable
    return PlanningData(
        demand=demand,
        prod_cost=prod_cost,
        hold_cost=hold_cost,
        setup_cost=setup_cost,
        capacity=capacity,
        initial_inventory=0.0,
    )


# (HELPER FUNCTION) to make each row of the report look nice.
# format_row: str List[float] -> str
def format_row(label, series):
    return label.ljust(14) + " ".join(f"{v:7.0f}" for v in series)

# Prints out the report comparing the optimized plan and the baseline plan so it looks nice.
# report: PlanningData PlanningResult PlanningResult -> float
def report(data, opt, base):
    # number of periods we're planning for
    num_periods = data.periods
    print("=" * 72)
    print("MULTI-PERIOD PRODUCTION & INVENTORY PLANNING  (lot-sizing MILP)")
    print("=" * 72)
    print(f"Horizon: {num_periods} periods | setup cost/period: {data.setup_cost[0]:.0f} "
          f"| holding cost/unit: {data.hold_cost[0]:.2f}")
    print()
    # show the demand for each period
    print(format_row("Period", list(range(1, num_periods + 1))))
    print(format_row("Demand", data.demand))
    print("-" * 72)
    # display the optimized production plan
    print("OPTIMIZED PLAN (MILP):")
    print(format_row("  Produce", opt.produce))
    print(format_row("  Inventory", opt.inventory))
    print(format_row("  Setup y_t", opt.setup))
    print(f"  # production runs: {sum(opt.setup)} of {num_periods} periods")
    print("-" * 72)
    # compare it against the simpler lot-for-lot approach
    print("BASELINE (lot-for-lot / produce-to-demand):")
    print(format_row("  Produce", base.produce))
    print(format_row("  Setup y_t", base.setup))
    print(f"  # production runs: {sum(base.setup)} of {num_periods} periods")
    print("=" * 72)
    # show where the savings are actually coming from
    print("COST COMPARISON")
    print(f"{'':20}{'Baseline':>14}{'Optimized':>14}{'Savings':>14}")
    for name, b, o in [
        ("Production", base.prod_cost_total, opt.prod_cost_total),
        ("Holding", base.hold_cost_total, opt.hold_cost_total),
        ("Setup", base.setup_cost_total, opt.setup_cost_total),
        ("TOTAL", base.total_cost, opt.total_cost),
    ]:
        print(f"{name:20}{b:14,.2f}{o:14,.2f}{b - o:14,.2f}")
    # calculate the percentage reduction in total cost
    pct = 100.0 * (base.total_cost - opt.total_cost) / base.total_cost
    print("-" * 72)
    print(f"Total cost reduction vs. baseline: "
          f"${base.total_cost - opt.total_cost:,.2f}  ({pct:.1f}%)")
    print("=" * 72)
    # return the final report
    return pct




# *** MAIN FUNCTION ***
# Runs the optimization model and compares its results against the baseline.
# main: Nat bool -> dict
def main(optional_seed=None, report_results=True):
    # Use the provided seed if one was given. Otherwise, use the default scenario.
    if optional_seed is not None:
        data = make_scenario(seed=optional_seed)
    else:
        data = make_scenario()
    # run both approaches on the exact same demand scenario
    opt = build_and_solve(data)  # from improved_strategy.py
    base = lot_for_lot(data)     # from baseline_strategy.py
    # make sure the optimized plan is never worse than the baseline
    assert opt.total_cost <= base.total_cost + 1e-6, "optimizer worse than baseline!"
    # Only print the report when requested. This is useful when testing lots of scenarios.
    if report_results:
        report(data, opt, base)
    return {"data": data, "opt": opt, "base": base}

# *** RUN THE PROJECT ***
if __name__ == "__main__":
    # Behavior is driven by the "config" dict at the top of this file, so a new
    # user can change what happens without touching any of the logic below.
    if config["test_consistency"]:
        # Test the optimizer against 999 different random scenarios
        all_savings = []
        for i in range(1, 1000):
            stats = main(optional_seed=i, report_results=False)
            # calculate how much cheaper the optimized plan was compared to the baseline
            savings = (stats["base"].total_cost - stats["opt"].total_cost) / stats["base"].total_cost
            all_savings.append(savings)
            # stop if the optimizer ever produces a worse result
            if savings < 0:
                print(f"Seed {i} produced a worse optimized plan than baseline!")
                print(f"  Base cost: {stats['base'].total_cost}")
                print(f"  Opt cost: {stats['opt'].total_cost}")
                break
        # show the average savings across all the scenarios we tested
        print(f"{sum(all_savings) / len(all_savings)} average savings over {len(all_savings)} random scenarios")
    else:
        # Just run a single scenario. test_seed = None uses the default scenario,
        # otherwise it picks the random scenario for that seed.
        main(optional_seed=config["test_seed"], report_results=config["report_results"])