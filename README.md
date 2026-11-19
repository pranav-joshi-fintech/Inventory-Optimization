# Inventory Optimization

A single-item production planner that schedules *how much to make and when* to meet demand at the lowest total cost. It implements the Wagner-Whitin dynamic program and measures it against a lot-for-lot baseline.

## The problem

Each week carries a random demand that must be met. Three costs compete:

- **Production** — per unit made
- **Holding** — per unit left in stock overnight
- **Setup** — a flat fee every time production runs at all

The setup fee is the tension. Producing one big batch and holding it avoids repeated setup fees but pays to store stock; producing weekly avoids storage but pays setup every week. Wagner-Whitin finds the split that minimizes the total, and it is provably optimal for this single-item case.

## Results

On the default 12-week scenario, Wagner-Whitin runs production 4 times instead of 12, cutting total cost by **23.7%**. Across 999 random scenarios it averages **~22.8%** savings and is never worse than the baseline.

![Cost by category](media/cost_comparison.png)
![Demand vs. production](media/demand_vs_production.png)

Full breakdown: [`media/sample_report.txt`](media/sample_report.txt) · raw plans and costs: [`media/results.xlsx`](media/results.xlsx)

## Run it

No third-party packages are needed to run the planner:

```bash
python main.py
```

Behavior is controlled by the `config` dict at the top of `main.py` (single scenario vs. the 999-scenario sweep, and whether to print the report).

Regenerating the files in `media/` additionally needs `matplotlib` and `openpyxl`:

```bash
pip install -r requirements.txt
python -m media.generate_media
```

## Layout

| File | Role |
| --- | --- |
| `main.py` | Builds scenarios, runs both strategies, prints the comparison |
| `improved_strategy.py` | Wagner-Whitin dynamic program |
| `baseline_strategy.py` | Lot-for-lot baseline |
| `planning_data.py` | Shared `PlanningData` and `Plan` data structures |

## Reference

Wagner-Whitin lot-sizing — [MIT OCW, Logistics Systems, Lecture 9](https://ocw.mit.edu/courses/esd-260j-logistics-systems-fall-2006/60025416518c3c513f34362c16d2f6ac_lect9.pdf)