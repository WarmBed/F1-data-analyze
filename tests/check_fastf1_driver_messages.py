import fastf1

fastf1.Cache.enable_cache('f1_analysis_cache')

print("檢查 FastF1 原始訊息中的車手資訊...\n")

session = fastf1.get_session(2023, 'Japan', 'R')
session.load()

msgs = session.race_control_messages

# 搜尋包含車手相關關鍵字的訊息
driver_keywords = ['CAR', 'INVOLVING', 'SPUN', 'ACCIDENT', 'COLLISION', 'OFF TRACK']
driver_msgs = msgs[msgs['Message'].str.contains('|'.join(driver_keywords), case=False, na=False)]

print(f"包含車手關鍵字的訊息數: {len(driver_msgs)}\n")
print("前 10 條訊息:")
print("=" * 80)

for idx, row in driver_msgs.head(10).iterrows():
    print(f"\n時間: {row['Time']}")
    print(f"類別: {row['Category']}")
    print(f"旗幟: {row['Flag']}")
    print(f"訊息: {row['Message']}")
