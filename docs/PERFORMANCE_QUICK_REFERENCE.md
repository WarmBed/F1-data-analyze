# Performance Optimization Quick Reference

**Quick lookup guide for common performance issues and solutions**

---

## 🚨 Critical: Replace `.iterrows()`

### ❌ Slow (100-800x slower)
```python
for _, row in df.iterrows():
    driver = row['Driver']
    position = row['Position']
    process(driver, position)
```

### ✅ Fast (Vectorized)
```python
# Option 1: Direct dict conversion
driver_positions = dict(zip(df['Driver'], df['Position']))

# Option 2: Use to_dict()
for record in df.to_dict('records'):
    process(record['Driver'], record['Position'])

# Option 3: Vectorized operations
df['result'] = df['Driver'].apply(lambda x: process(x))
```

---

## 🔥 Replace `.apply(axis=1)`

### ❌ Slow
```python
df['category'] = df['race'].apply(get_category)
df['result'] = df.apply(lambda row: func(row['a'], row['b']), axis=1)
```

### ✅ Fast
```python
# Use .map() for single column
df['category'] = df['race'].map(get_category)

# Or vectorize with np.where
df['result'] = np.where(df['a'] > df['b'], 'A', 'B')

# Or use .map() with dict
category_map = {race: get_category(race) for race in df['race'].unique()}
df['category'] = df['race'].map(category_map)
```

---

## 🎯 Optimize DataFrame Indexing

### ❌ Slow
```python
fastest_lap = valid_laps.loc[valid_laps['LapTime'].idxmin()]
slowest_lap = valid_laps.loc[valid_laps['LapTime'].idxmax()]
```

### ✅ Fast
```python
# Cache the index
fastest_idx = valid_laps['LapTime'].idxmin()
slowest_idx = valid_laps['LapTime'].idxmax()
fastest_lap = valid_laps.loc[fastest_idx]
slowest_lap = valid_laps.loc[slowest_idx]

# Or use nsmallest/nlargest
fastest_laps = valid_laps.nsmallest(1, 'LapTime')
```

---

## 💾 Add Caching

### ❌ No Cache
```python
def get_session_data(year, race, session):
    data = api.fetch(year, race, session)  # Slow API call every time
    return data
```

### ✅ Cached
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_session_data(year, race, session):
    data = api.fetch(year, race, session)
    return data
```

---

## 🌐 Parallel API Requests

### ❌ Sequential
```python
results = []
for session in ['FP1', 'FP2', 'FP3', 'Q', 'R']:
    data = fetch_session(session)  # 5 seconds each = 25 seconds total
    results.append(data)
```

### ✅ Parallel
```python
from concurrent.futures import ThreadPoolExecutor

def fetch_all_sessions():
    with ThreadPoolExecutor(max_workers=5) as executor:
        sessions = ['FP1', 'FP2', 'FP3', 'Q', 'R']
        results = list(executor.map(fetch_session, sessions))  # 5 seconds total
    return results
```

---

## 🖥️ Non-Blocking GUI

### ❌ Blocks GUI
```python
def on_button_click(self):
    time.sleep(2)  # Freezes GUI for 2 seconds
    data = requests.get(url)  # Blocks until complete
    self.update_display(data)
```

### ✅ Non-Blocking
```python
def on_button_click(self):
    # Use QTimer instead of sleep
    QTimer.singleShot(2000, self.delayed_action)
    
    # Use worker thread for network
    worker = ApiWorker(url)
    worker.finished.connect(self.update_display)
    worker.start()  # Non-blocking
```

---

## 📦 Avoid Unnecessary Copies

### ❌ Extra Memory
```python
temp = df.copy()  # Full copy (slow, uses 2x memory)
result = temp[temp['value'] > 0]
```

### ✅ Memory Efficient
```python
# Views are created automatically for filters
result = df[df['value'] > 0]  # No copy needed

# Only copy when modifying in-place
if need_to_modify:
    temp = df.copy()  # Now justified
    temp['new_col'] = temp['old_col'] * 2
```

---

## 📄 Faster JSON

### ❌ Standard JSON
```python
import json
with open('data.json', 'w') as f:
    json.dump(data, f)  # Slow for large files
```

### ✅ Fast JSON
```python
import orjson  # 2-3x faster

with open('data.json', 'wb') as f:
    f.write(orjson.dumps(data))
```

---

## 🔄 Efficient String Building

### ❌ Slow Concatenation
```python
result = ""
for item in items:
    result += f"{item}, "  # Creates new string each iteration
```

### ✅ Fast Join
```python
result = ", ".join(str(item) for item in items)
```

---

## 🎨 Batch GUI Updates

### ❌ Updates During Loop
```python
for i in range(1000):
    table.insertRow(i)
    # Redraws 1000 times
```

### ✅ Batch Update
```python
table.setUpdatesEnabled(False)
for i in range(1000):
    table.insertRow(i)
table.setUpdatesEnabled(True)  # Redraws once
```

---

## 📊 NumPy for Numerical Operations

### ❌ Python Loop
```python
result = []
for speed in speeds:
    result.append(speed * 3.6)  # km/h conversion
```

### ✅ NumPy
```python
import numpy as np
result = np.array(speeds) * 3.6  # 10-100x faster
```

---

## 🔍 Lazy Module Loading

### ❌ Load Everything at Startup
```python
# At top of file
from heavy_module import *  # Slow startup
import ml_library  # May not be needed
```

### ✅ Load When Needed
```python
# At top of file - only what's always needed
from lightweight_module import Class1

# Inside function - only load when called
def train_model():
    import ml_library  # Only loaded if function called
    return ml_library.train()
```

---

## 🗃️ Efficient Data Storage

### ❌ CSV for Large Data
```python
df.to_csv('large_data.csv')  # Slow read/write
df = pd.read_csv('large_data.csv')
```

### ✅ Parquet Format
```python
df.to_parquet('data.parquet', compression='snappy')  # 10x faster
df = pd.read_parquet('data.parquet', columns=['col1', 'col2'])  # Selective loading
```

---

## 🧹 Memory Management

### ❌ Memory Leaks
```python
class Worker(QThread):
    def run(self):
        self.big_data = load_huge_dataset()
        # Never released!
```

### ✅ Cleanup
```python
class Worker(QThread):
    def run(self):
        self.big_data = load_huge_dataset()
        # Process data...
    
    def cleanup(self):
        self.big_data = None  # Release reference
        self.deleteLater()  # Schedule deletion
```

---

## 📈 Profile Your Code

### Quick Profiling
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
analyze_race(2025, 'Japan', 'R')

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

### Memory Profiling
```python
from memory_profiler import profile

@profile
def my_function():
    # Shows line-by-line memory usage
    data = load_large_dataset()
    return process(data)
```

---

## 🎯 Priority Checklist

When optimizing, check in this order:

1. ✅ Replace all `.iterrows()` → **Biggest impact**
2. ✅ Add `@lru_cache` to pure functions
3. ✅ Fix GUI blocking operations
4. ✅ Parallelize independent operations
5. ✅ Use vectorized pandas operations
6. ✅ Implement proper caching
7. ✅ Batch database/API calls
8. ✅ Use efficient data formats (parquet vs CSV)
9. ✅ Profile to find actual bottlenecks
10. ✅ Monitor memory usage

---

## 🔧 Quick Commands

### Profile a script:
```bash
python -m cProfile -o output.prof script.py
python -m pstats output.prof
# Then: sort cumulative, stats 20
```

### Memory profile:
```bash
python -m memory_profiler script.py
```

### Line profiling:
```bash
kernprof -l -v script.py
```

---

## 📚 See Also

- Full analysis: `docs/PERFORMANCE_ANALYSIS.md`
- Pandas performance: https://pandas.pydata.org/docs/user_guide/enhancingperf.html
- Python profiling: https://docs.python.org/3/library/profile.html

---

*Keep this reference handy while coding!*
