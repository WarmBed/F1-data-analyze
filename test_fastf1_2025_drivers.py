#!/usr/bin/env python3
"""測試 FastF1 的 2025 車手數據"""

import fastf1
from fastf1.ergast import Ergast

print('FastF1 version:', fastf1.__version__)

# 嘗試使用 ergast 接口
ergast = Ergast()

try:
    standings = ergast.get_driver_standings(season=2025, round='last')
    print('2025 standings available:', standings is not None)
    
    if standings and hasattr(standings, 'content') and standings.content:
        df = standings.content[0]
        print('Columns:', list(df.columns))
        print('\n=== 2025 Driver Standings (from Ergast) ===')
        for _, row in df.head(22).iterrows():
            code = row.get('driverCode', 'N/A')
            given = row.get('givenName', '')
            family = row.get('familyName', '')
            name = f"{given} {family}"
            teams = row.get('constructorNames', ['Unknown'])
            team = teams[0] if isinstance(teams, list) and teams else str(teams)
            print(f'{code}: {name} - {team}')
    else:
        print('No standings content found')
        
except Exception as e:
    print(f'Error with 2025: {e}')
    print('\nTrying 2024 as fallback...')
    try:
        standings = ergast.get_driver_standings(season=2024, round='last')
        if standings and hasattr(standings, 'content') and standings.content:
            df = standings.content[0]
            print('\n=== 2024 Driver Standings (fallback) ===')
            for _, row in df.head(22).iterrows():
                code = row.get('driverCode', 'N/A')
                given = row.get('givenName', '')
                family = row.get('familyName', '')
                name = f"{given} {family}"
                teams = row.get('constructorNames', ['Unknown'])
                team = teams[0] if isinstance(teams, list) and teams else str(teams)
                print(f'{code}: {name} - {team}')
    except Exception as e2:
        print(f'Error with 2024: {e2}')

# 檢查 OpenF1 API (如果可用)
print('\n\n=== Checking for OpenF1 driver data ===')
try:
    import requests
    response = requests.get('https://api.openf1.org/v1/drivers?session_key=latest', timeout=10)
    if response.status_code == 200:
        drivers = response.json()
        print(f'OpenF1 returned {len(drivers)} drivers:')
        seen = set()
        for d in drivers:
            code = d.get('name_acronym', 'N/A')
            if code in seen:
                continue
            seen.add(code)
            name = d.get('full_name', 'Unknown')
            team = d.get('team_name', 'Unknown')
            print(f'{code}: {name} - {team}')
except Exception as e:
    print(f'OpenF1 error: {e}')
