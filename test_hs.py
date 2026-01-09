from strategy_simulator.gui.widgets.strategy_report_generator import StrategyReportGenerator

gen = StrategyReportGenerator()

# Test H-S strategy (from user's report)
stints = gen._parse_stints_from_name('H-S', 58)
print(f'H-S strategy: {len(stints)} stints')
for i, s in enumerate(stints, 1):
    print(f'  Stint {i}: {s.compound.value} - {s.planned_length} laps')
