# planning_data.py
# Don't run this file directly.

"""
FILE PURPOSE:
-------------
Both strategies need a format for their input and output, which this file defines.
The following are the two things that both strategies need to agree on:
 - what a problem looks like (PlanningData: the demand, the costs, etc.)
 - what an answer looks like (Plan: how much to make/hold, and the bill)
"""

# *** IMPORTS ***
from dataclasses import dataclass
from typing import List


# *** DATA DEFINITIONS ***
"""
"PlanningData" holds everything the problem needs: the demand we have to meet,
what it costs to produce / hold / set up each period, how much we can make, and
what's already in stock on day one.

PlanningData:
    demand: (listof float) - The demand for each period.
    prod_cost: (listof float) - The production cost per unit for each period.
    hold_cost: (listof float) - The holding cost per unit for each period.
    setup_cost: (listof float) - The flat setup cost for producing in each period.
    capacity: (listof float) - The production capacity for each period.
    initial_inventory: float - The initial inventory level.

"Plan" is the answer: how much to produce and hold each period, whether we ran
a setup, and the costs broken out so main.py can print a tidy comparison.

A "Nat" is an Int that is >=1.
"""

@dataclass
class PlanningData:
    demand: List[float]
    prod_cost: List[float]
    hold_cost: List[float]
    setup_cost: List[float]
    capacity: List[float]
    initial_inventory: float = 0.0
    # periods is the number of periods we're planning for, which is the length of the demand list.
    @property
    def periods(self) -> int:
        return len(self.demand)
@dataclass
class Plan:
    produce: List[float] # x_t -> units produced in period t
    inventory: List[float] # I_t -> units left in stock at the end of period t
    setup: List[int] # y_t -> 1 if we produced in t, else 0
    total_cost: float
    prod_cost_total: float
    hold_cost_total: float
    setup_cost_total: float

# *** If this file is run directly ***
if __name__ == "__main__":
    print("This file is not meant to be run directly. "
          "It just holds the shared data structures for both strategies.")