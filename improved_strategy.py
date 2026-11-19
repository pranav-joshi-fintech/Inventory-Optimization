# improved_strategy.py
# Don't run this file directly.
"""
FILE PURPOSE:
-------------
This is the smart approach to this lot-sizing problem, called the Wagner-Whitin strategy. In this
strategy, we don't produce the same amount every period. We work out how much to produce and when,
so that we meet all demand for the lowest total cost across production, holding, and setup fees.

For instance, pretend a setup fee of 500 is charged every time we produce at all, and holding one
item overnight costs 1. Then, let's say demand is 100 items per week for 4 weeks. Buying fresh each
week pays the setup fee 4 times (2000). Instead we can produce all 400 items in week 1 and pay the
setup fee once (500), even after paying to hold the extra 300, then 200, then 100 items.

This works because of the Wagner-Whitin result: in the cheapest plan, we only ever produce when
stock has run down to zero, so each run covers a block of back-to-back periods. That lets us chop
the timeline into blocks and pick the cheapest chopping with dynamic programming, which is provably
optimal for a single item with no external dependencies.

*Note: Even though this buys whenever stock is approaching zero, this strategy is still
dynamically smart because it algorithmically determines HOW MUCH to buy each time,
rather than just buying the next period's demand. It can buy enough to cover multiple periods
if that is cheaper.

Source: https://ocw.mit.edu/courses/esd-260j-logistics-systems-fall-2006/60025416518c3c513f34362c16d2f6ac_lect9.pdf
^^^ This is also in README.md
"""

# *** IMPORTS ***
from typing import List, Tuple
# PlanningData and Plan are the formats by which both strategies should structure
# their input and output.
from planning_data import PlanningData, Plan




# *** THE IMPROVED STRATEGY ***
# Work out the cheapest production plan using the Wagner-Whitin idea above.
def solve_lot_sizing(
    demand: List[float],
    prod_cost: List[float],
    hold_cost: List[float],
    setup_cost: List[float],
    capacity: List[float],
    initial_inventory: float = 0.0,
) -> Tuple[List[float], List[float], List[int], float]:
    periods = len(demand)
    # use up whatever we already have in stock against the earliest demand, for free
    net_demand = list(demand)
    current_inventory = initial_inventory
    for period in range(periods):
        used = min(current_inventory, net_demand[period])
        net_demand[period] -= used
        current_inventory -= used
        if current_inventory <= 0:
            break
    # cost of covering periods start..end with one run at start, or None if over capacity
    def cost_to_cover(start, end):
        quantity = sum(net_demand[start:end + 1])
        if quantity > capacity[start] + 1e-9:
            return None
        cost = setup_cost[start] if quantity > 1e-9 else 0.0
        cost += prod_cost[start] * quantity
        for period in range(start, end + 1):
            held_periods = period - start
            cost += hold_cost[start] * net_demand[period] * held_periods
        return cost
    # cheapest[t] is the cheapest way to cover demand from period t to the end
    INF = float("inf")
    cheapest = [INF] * (periods + 1)
    block_end = [-1] * (periods + 1)
    cheapest[periods] = 0.0
    for start in range(periods - 1, -1, -1):
        if net_demand[start] <= 1e-9:
            # nothing due this period, so producing nothing and rolling forward is free
            if cheapest[start + 1] < cheapest[start]:
                cheapest[start] = cheapest[start + 1]
                block_end[start] = start
        for end in range(start, periods):
            block_cost = cost_to_cover(start, end)
            if block_cost is None:
                break
            total = block_cost + cheapest[end + 1]
            if total < cheapest[start] - 1e-9:
                cheapest[start] = total
                block_end[start] = end
    # walk the choices forward to turn them back into an actual production plan
    produce = [0.0] * periods
    setup = [0] * periods
    period = 0
    while period < periods:
        end = block_end[period]
        if end == -1:
            period += 1
            continue
        quantity = sum(net_demand[period:end + 1])
        produce[period] = round(quantity, 6)
        setup[period] = 1 if quantity > 1e-9 else 0
        period = end + 1
    # replay the plan against the original demand to get the real end-of-period stock
    inventory = [0.0] * periods
    current_inventory = initial_inventory
    for period in range(periods):
        current_inventory = current_inventory + produce[period] - demand[period]
        inventory[period] = round(max(0.0, current_inventory), 6)
        current_inventory = inventory[period]
    total_cost = round(cheapest[0], 2)
    return produce, inventory, setup, total_cost




# *** THE FRONT DOOR ***
# Hand the raw numbers to the optimizer above, then total the cost by category.
# build_and_solve: PlanningData -> Plan
def build_and_solve(data: PlanningData) -> Plan:
    produce, inventory, setup, _ = solve_lot_sizing(
        demand=data.demand,
        prod_cost=data.prod_cost,
        hold_cost=data.hold_cost,
        setup_cost=data.setup_cost,
        capacity=data.capacity,
        initial_inventory=data.initial_inventory,
    )
    periods = data.periods
    # add up each cost bucket separately so main.py can break them out
    prod_costs = sum(data.prod_cost[period] * produce[period] for period in range(periods)) # production
    hold_costs = sum(data.hold_cost[period] * inventory[period] for period in range(periods)) # holding
    setup_costs = sum(data.setup_cost[period] * setup[period] for period in range(periods)) # setup
    return Plan(
        produce=produce,
        inventory=inventory,
        setup=setup,
        total_cost=round(prod_costs + hold_costs + setup_costs, 2),
        prod_cost_total=round(prod_costs, 2),
        hold_cost_total=round(hold_costs, 2),
        setup_cost_total=round(setup_costs, 2),
    )


# *** If this file is run directly ***
if __name__ == "__main__":
    print("This file is not meant to be run directly. "
          "It is imported by main.py to provide the optimized strategy.")
