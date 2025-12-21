import fastf1
import pandas as pd
from datetime import datetime, timezone

# 取得 2025 年賽程
schedule = fastf1.get_event_schedule(2025)
vegas = schedule[schedule['EventName'] == 'Las Vegas Grand Prix'].iloc[0]

# 解析賽事日期
race_date = pd.to_datetime(vegas['Session5DateUtc'])
if race_date.tzinfo is None:
    race_date = race_date.replace(tzinfo=timezone.utc)

now = datetime.now(timezone.utc)

print(f"Race date: {race_date}")
print(f"Now: {now}")
print(f"Is future: {race_date > now}")
print(f"Days until race: {(race_date - now).days}")
