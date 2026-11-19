# baseline_strategy.py
# Don't run this file directly.
"""
FILE PURPOSE:
-------------
This is the most straightforward approach to this lot-sizing problem. In this strategy, we produce
exactly what we need to meet demand in each period, and we hold nothing back. This is often called
a "lot-for-lot" approach, because we only buy a lot of goods for every lot sold.

For instance, pretend we have items_sold ~ normal-distribution(mean=100, variance=50), and assume
we currently have 200 items in stock. Then, let's say that in the first week, we sold 120 items,
leaving 80 in stock. In this strategy, we would buy another 80 stock at the end of the week in
preparation for the next week.

Obviously, this system is inefficient in that it's not properly adjusting how much it's buying
depending on whether overbuying+shelving or buying nothing is more advantageous on each day.
"""

# *** IMPORTS ***
# PlanningData and Plan are the formats by which both strategies should structure
# their input and output.
from planning_data import PlanningData, Plan




# *** THE BASELINE STRATEGY ***
# Produce exactly this period's demand, every period, holding nothing back.
# lot_for_lot: PlanningData -> Plan
def lot_for_lot(data: PlanningData) -> Plan:
    periods = data.periods
    produce = [0.0] * periods
    inventory = [0.0] * periods
    setup = [0] * periods
    current_inventory = data.initial_inventory
    for period in range(periods):
        # make just enough to cover demand, after using up anything in stock
        need = max(0.0, data.demand[period] - current_inventory)
        produce[period] = need
        setup[period] = 1 if need > 1e-9 else 0 # any production at all = one setup fee
        current_inventory = current_inventory + produce[period] - data.demand[period]
        inventory[period] = current_inventory
    # total up each cost bucket the same way the optimizer does
    prod_costs = sum(data.prod_cost[period] * produce[period] for period in range(periods)) # production
    hold_costs = sum(data.hold_cost[period] * inventory[period] for period in range(periods)) # holding (should be ~0 here)
    setup_costs = sum(data.setup_cost[period] * setup[period] for period in range(periods)) # setup
    return Plan(
        produce=[round(value, 6) for value in produce],
        inventory=[round(value, 6) for value in inventory],
        setup=setup,
        total_cost=round(prod_costs + hold_costs + setup_costs, 2),
        prod_cost_total=round(prod_costs, 2),
        hold_cost_total=round(hold_costs, 2),
        setup_cost_total=round(setup_costs, 2),
    )


# *** If this file is run directly ***
if __name__ == "__main__":
    print("This file is not meant to be run directly. "
          "It is imported by main.py to provide the baseline strategy for comparison.")