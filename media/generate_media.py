# generate_media.py
# Run from the project root: python -m media.generate_media
"""
FILE PURPOSE:
-------------
This file builds the artifacts in /media straight from the live project code, so the numbers in the
readme always match what the code actually produces. It writes a cost-comparison chart, a demand vs.
production chart, an Excel workbook of the plans, and a captured console report.

For instance, running this on the default 12-week scenario writes cost_comparison.png showing the
setup cost dropping from 4,800 to 1,600, and results.xlsx holding the week-by-week plan behind it.
"""

# *** IMPORTS ***
import io
import os
from contextlib import redirect_stdout
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
# build_and_solve and lot_for_lot are the two strategies, make_scenario and report come from main.
from improved_strategy import build_and_solve
from baseline_strategy import lot_for_lot
from main import make_scenario, report


# *** WHERE THE ARTIFACTS GO ***
media_dir = os.path.dirname(os.path.abspath(__file__))


# *** BUILD THE DEFAULT SCENARIO ***
# run both strategies on the same default scenario so every artifact agrees
data = make_scenario()
opt = build_and_solve(data)
base = lot_for_lot(data)
periods = data.periods


# *** CAPTURE THE CONSOLE REPORT ***
# redirect the report's prints into a string so we can save it to a file
buffer = io.StringIO()
with redirect_stdout(buffer):
    report(data, opt, base)
report_text = buffer.getvalue()
with open(os.path.join(media_dir, "sample_report.txt"), "w", encoding="utf-8") as report_file:
    report_file.write(report_text)


# *** COST-COMPARISON CHART ***
# one bar per cost bucket, simple plan against smart plan
categories = ["Making", "Storage", "Setup fees", "TOTAL"]
base_costs = [base.prod_cost_total, base.hold_cost_total, base.setup_cost_total, base.total_cost]
opt_costs = [opt.prod_cost_total, opt.hold_cost_total, opt.setup_cost_total, opt.total_cost]
positions = range(len(categories))
bar_width = 0.38
figure, axes = plt.subplots(figsize=(8, 4.5))
axes.bar([p - bar_width / 2 for p in positions], base_costs, bar_width, label="Simple plan (make weekly)", color="#b0b0b0")
axes.bar([p + bar_width / 2 for p in positions], opt_costs, bar_width, label="Smart plan (Wagner-Whitin)", color="#2f6f4f")
axes.set_ylabel("Cost ($)")
axes.set_title("Where the money goes: simple plan vs. smart plan (12 weeks)")
axes.set_xticks(list(positions))
axes.set_xticklabels(categories)
axes.legend()
figure.tight_layout()
figure.savefig(os.path.join(media_dir, "cost_comparison.png"), dpi=150)
plt.close(figure)


# *** DEMAND VS PRODUCTION CHART ***
# demand as bars, the smart plan's production as a line spiking ahead of demand
weeks = list(range(1, periods + 1))
figure, axes = plt.subplots(figsize=(8, 4.5))
axes.bar(weeks, data.demand, color="#cccccc", label="Weekly demand")
axes.plot(weeks, opt.produce, marker="o", color="#2f6f4f", label="Smart plan: units made")
axes.set_xlabel("Week")
axes.set_ylabel("Units")
axes.set_title("The smart plan makes a few big batches instead of producing every week")
axes.set_xticks(weeks)
axes.legend()
figure.tight_layout()
figure.savefig(os.path.join(media_dir, "demand_vs_production.png"), dpi=150)
plt.close(figure)


# *** EXCEL WORKBOOK ***
# a workbook a non-technical reader can open and understand without the code
dollars = "$#,##0.00"
title_font = Font(bold=True, size=14)
bold = Font(bold=True)
wrap = Alignment(wrap_text=True, vertical="top")
savings = base.total_cost - opt.total_cost
percent_saved = 100.0 * savings / base.total_cost
base_runs = sum(base.setup)
opt_runs = sum(opt.setup)
# how many weeks each production run covers, used to narrate the weekly plan
run_spans = []
run_start = None
for week in range(periods):
    if opt.setup[week] == 1:
        if run_start is not None:
            run_spans.append((run_start, week - 1))
        run_start = week
if run_start is not None:
    run_spans.append((run_start, periods - 1))
covered_by = [0] * periods
for span_start, span_end in run_spans:
    covered_by[span_start] = span_end

# Summary sheet, the first thing the reader sees
workbook = Workbook()
summary = workbook.active
summary.title = "Summary"
summary.column_dimensions["A"].width = 95
summary["A1"] = "Inventory Optimization - Results Summary"
summary["A1"].font = title_font
summary_lines = [
    "",
    "The problem: we have to meet customer demand every week for 12 weeks. Making a batch of product",
    "costs a flat fee every time (like setting up a machine), plus a per-unit cost. Anything we make",
    "early and don't sell yet costs money to store. So do we make small batches often, or big batches",
    "rarely? This tool finds the cheapest answer.",
    "",
    f"The result: the smart plan (Wagner-Whitin) meets the exact same demand for ${opt.total_cost:,.2f}",
    f"instead of the simple plan's ${base.total_cost:,.2f} - a saving of ${savings:,.2f} ({percent_saved:.1f}%).",
    "",
    f"How: it runs production only {opt_runs} times across the 12 weeks instead of all {base_runs} weeks,",
    "making bigger batches up front. It pays a little more to store that stock, but avoids most of the",
    "setup fees, and the fees were the bigger cost.",
    "",
    "What's in this file:",
    "   - Weekly Plan:    week by week, what each plan makes and holds, in plain language.",
    "   - Cost Breakdown: where the money goes, and why the smart plan wins.",
    "   - Glossary:       what every term and number means.",
]
for line in summary_lines:
    summary.append([line])

# Weekly Plan sheet, narrated
plan_sheet = workbook.create_sheet("Weekly Plan")
plan_headers = ["Week", "Customer demand (units)", "Smart plan: units made", "Smart plan: units in storage", "Simple plan: units made", "What the smart plan did"]
plan_sheet.append(plan_headers)
for header_cell in plan_sheet[1]:
    header_cell.font = bold
    header_cell.alignment = wrap
for week in range(periods):
    if opt.setup[week] == 1:
        span_end = covered_by[week]
        if span_end == week:
            note = f"Made a batch this week for week {week + 1}"
        else:
            note = f"Made one big batch covering weeks {week + 1}-{span_end + 1}"
    else:
        note = "No production - selling from stock made earlier"
    plan_sheet.append([week + 1, data.demand[week], opt.produce[week], opt.inventory[week], base.produce[week], note])
plan_sheet.column_dimensions["A"].width = 6
for column_letter in ["B", "C", "D", "E"]:
    plan_sheet.column_dimensions[column_letter].width = 16
plan_sheet.column_dimensions["F"].width = 44
for row in plan_sheet.iter_rows(min_row=2):
    row[5].alignment = wrap

# Cost Breakdown sheet, with a plain reason on every line
cost_sheet = workbook.create_sheet("Cost Breakdown")
cost_sheet.append(["Cost type", "Simple plan", "Smart plan", "Saving", "Why"])
for header_cell in cost_sheet[1]:
    header_cell.font = bold
    header_cell.alignment = wrap
cost_rows = [
    ("Making the product", base.prod_cost_total, opt.prod_cost_total, "Same total units are made either way, so this cost is identical."),
    ("Storing stock", base.hold_cost_total, opt.hold_cost_total, "The smart plan makes ahead and stores more, so this cost goes UP. That's the trade-off."),
    ("Setup fees", base.setup_cost_total, opt.setup_cost_total, "The flat fee per production run. Fewer runs means far fewer fees - this is the big win."),
    ("TOTAL", base.total_cost, opt.total_cost, "Extra storage cost is small next to the setup fees saved, so the total drops."),
]
for name, base_value, opt_value, why in cost_rows:
    cost_sheet.append([name, base_value, opt_value, round(base_value - opt_value, 2), why])
for row in cost_sheet.iter_rows(min_row=2):
    for money_cell in row[1:4]:
        money_cell.number_format = dollars
    row[4].alignment = wrap
for total_cell in cost_sheet[cost_sheet.max_row]:
    total_cell.font = bold
cost_sheet.column_dimensions["A"].width = 20
for column_letter in ["B", "C", "D"]:
    cost_sheet.column_dimensions[column_letter].width = 14
cost_sheet.column_dimensions["E"].width = 60

# Glossary sheet, defines every term a reader might trip on
glossary_sheet = workbook.create_sheet("Glossary")
glossary_sheet.append(["Term", "What it means"])
for header_cell in glossary_sheet[1]:
    header_cell.font = bold
glossary_rows = [
    ("Demand", "How many units customers want that week. We must always meet it."),
    ("Simple plan (lot-for-lot)", "Make exactly what's needed each week. Easy, but pays a setup fee every single week."),
    ("Smart plan (Wagner-Whitin)", "Make bigger batches less often when that's cheaper overall. Provably the lowest-cost plan."),
    ("Units made", "How many units a plan produces that week. Zero means it's selling from earlier stock."),
    ("Units in storage", "Units left on the shelf at week's end, waiting to be sold. Each one costs a holding fee."),
    ("Setup fee", f"A flat ${data.setup_cost[0]:,.0f} charged every time production runs, no matter the batch size."),
    ("Making cost", f"${data.prod_cost[0]:,.2f} per unit produced."),
    ("Holding cost", f"${data.hold_cost[0]:,.2f} per unit left in storage at the end of a week."),
    ("Scenario", "A fixed 12-week demand pattern used so both plans are compared on identical conditions."),
]
for term, meaning in glossary_rows:
    glossary_sheet.append([term, meaning])
glossary_sheet.column_dimensions["A"].width = 30
glossary_sheet.column_dimensions["B"].width = 80
for row in glossary_sheet.iter_rows(min_row=2):
    row[1].alignment = wrap

workbook.save(os.path.join(media_dir, "results.xlsx"))
print("wrote sample_report.txt, cost_comparison.png, demand_vs_production.png, results.xlsx")
