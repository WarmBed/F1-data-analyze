"""检查China和Qatar在2022-2024的赛事历史"""
import fastf1

print("检查 China 和 Qatar 在 2022-2024 是否有足够的历史数据用于训练模型...")
print("=" * 80)

years = [2022, 2023, 2024]
races = ['China', 'Qatar']

for race in races:
    print(f"\n{race}:")
    print("-" * 40)
    
    for year in years:
        try:
            schedule = fastf1.get_event_schedule(year)
            event = schedule[schedule['EventName'].str.contains(race, case=False)]
            
            if not event.empty:
                event_name = event['EventName'].iloc[0]
                event_format = event['EventFormat'].iloc[0]
                print(f"  {year}: {event_name:30s} - {event_format}")
            else:
                print(f"  {year}: 无赛事")
                
        except Exception as e:
            print(f"  {year}: Error - {e}")

print("\n" + "=" * 80)
print("结论：")
print("- China: 2019年后因COVID-19取消，2024年回归但为冲刺赛周末")
print("- Qatar: 2021年首次举办，历史数据有限")
print("建议：这两场赛事可能需要使用通用模型或邻近赛道的模型")
