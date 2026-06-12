from CLI_modules.cli.analyzer.season_calendar_analysis import generate_season_calendar

print('Running generate_season_calendar for 2026 (force=True)')
result = generate_season_calendar(2026, save_json=True, force=True)
print('Result:', result)
