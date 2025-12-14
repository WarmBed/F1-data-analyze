"""
Debug CarData structure
"""
import requests
import base64
import zlib
import json
from core.logger import get_logger

logger = get_logger(component="gui")

def decode_f1_packet(raw_b64_string):
    try:
        decoded_bytes = base64.b64decode(raw_b64_string)
        decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
        return json.loads(decompressed_bytes.decode('utf-8'))
    except:
        return None

url = "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/CarData.z.jsonStream"
response = requests.get(url, timeout=60)
content = response.content

text = content.decode('utf-8-sig')
lines = text.split('\r\n')
lines = [line for line in lines if line.strip()]

# 看第一筆記錄的結構
line = lines[0]
timestamp = line[:12]
decoded = decode_f1_packet(line[12:])

logger.info("First CarData record structure:")
logger.info(f"Timestamp: {timestamp}")
logger.info(f"Data keys: {decoded.keys() if decoded else 'None'}")

if decoded and 'Entries' in decoded:
    logger.info(f"Entries: {len(decoded['Entries'])}")
    entry = decoded['Entries'][0]
    logger.info(f"Entry keys: {entry.keys()}")
    logger.info(f"Entry Utc: {entry.get('Utc', 'N/A')}")
    
    cars = entry.get('Cars', {})
    logger.info(f"Cars in entry: {list(cars.keys())}")
    
    if '44' in cars:
        logger.info(f"Car 44 data: {cars['44']}")
    elif cars:
        first_car = list(cars.keys())[0]
        logger.info(f"First car ({first_car}) data: {cars[first_car]}")
