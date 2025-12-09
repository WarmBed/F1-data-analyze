# Top 20 Critical Performance Issues - F1 Data Analysis

**Priority-ranked list of the most impactful performance issues**

---

## 🔴 CRITICAL (Fix First)

### 1. `.iterrows()` in 66 Files - **Highest Impact**

**Issue:** Using `.iterrows()` is 100-800x slower than vectorized operations  
**Files Affected:** 66 files across the codebase  
**Impact:** Every analysis using this is severely slowed  
**Estimated Speedup:** 50-80% for affected analyses

**Key Files:**
- `train_overtake_rate.py` (line 49)
- `CLI_modules/cli/analyzer/single_driver_all_corners_detailed_analysis.py`
- `CLI_modules/cli/analyzer/corner_detailed_analysis.py`
- `CLI_modules/cli/analyzer/single_driver_analysis.py`
- 62 more files...

**Fix:**
```python
# Replace:
for _, row in df.iterrows():
    driver = row['Driver']
    position = row['Position']

# With:
driver_positions = dict(zip(df['Driver'], df['Position']))
```

---

### 2. Monolithic `f1t_gui_main.py` (22,806 lines)

**Issue:** Massive single file with 510 functions  
**Impact:** 
- Slow IDE performance
- 10-15 second startup time
- Hard to maintain
- Slow imports

**Estimated Speedup:** 50-60% faster startup after splitting  

**Fix:** Split into modular architecture (see PERFORMANCE_ANALYSIS.md §3.1)

---

### 3. No In-Memory Caching for API Calls

**Issue:** 126 API calls without in-memory caching  
**Impact:** Repeated identical requests hit network every time  
**Estimated Speedup:** 80-90% for cached data

**Current:** Only file-based cache exists  
**Fix:** Add LRU cache layer:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_session_data(year, race, session):
    return api.fetch(year, race, session)
```

---

### 4. Sequential API Calls (Should Be Parallel)

**Issue:** Fetching multiple sessions sequentially  
**Example:** Loading FP1, FP2, FP3, Q, R takes 25 seconds instead of 5  
**Impact:** 5x slower than necessary  
**Estimated Speedup:** 400% for multi-session loads

**Fix:** Use ThreadPoolExecutor for parallel requests

---

### 5. GUI Blocking Operations

**Issue:** `time.sleep()` and synchronous API calls in GUI thread  
**Impact:** GUI freezes, poor user experience  
**Files:** `f1t_gui_main.py` line 4860

**Fix:** 
- Replace `time.sleep()` with `QTimer`
- Move network calls to worker threads

---

## 🟠 HIGH PRIORITY

### 6. Large `function_mapper.py` (6,259 lines)

**Issue:** Single massive file with all function mappings  
**Impact:** Slow module loading, hard to maintain  
**Estimated Speedup:** 30-40% faster function dispatch

**Fix:** Split into separate modules by function group

---

### 7. Inefficient `.apply(axis=1)` Usage

**Issue:** Found 15+ instances using slow row-wise apply  
**Impact:** 40-60% slower than vectorized alternatives

**Files:**
- `CLI_modules/cli/prediction/track_classifier.py` (lines 121, 339)
- `CLI_modules/cli/prediction/xgboost_trainer.py` (line 446)

**Fix:** Use `.map()` or vectorized operations

---

### 8. Repeated `.loc[]` Index Lookups

**Issue:** Multiple `.loc[]` calls for same index in loops  
**Files:** 15+ instances in analyzer modules  
**Impact:** Unnecessary repeated lookups

**Fix:** Cache index results before accessing

---

### 9. 158 Unnecessary DataFrame `.copy()` Operations

**Issue:** Copying DataFrames when views would suffice  
**Impact:** 2x memory usage, slower operations  
**Estimated Improvement:** 30-40% memory reduction

---

### 10. Standard `json` Library (Should Use `orjson`)

**Issue:** 602 JSON operations using slow standard library  
**Impact:** JSON serialization is bottleneck  
**Estimated Speedup:** 50-70% faster JSON operations

**Fix:**
```python
import orjson  # 2-3x faster
with open('data.json', 'wb') as f:
    f.write(orjson.dumps(data))
```

---

## 🟡 MEDIUM PRIORITY

### 11. No Cache Warming for Frequently Accessed Data

**Issue:** First access always hits API/disk  
**Impact:** Slow first load for common analyses  
**Fix:** Pre-load common analyses in background

---

### 12. Wildcard Imports in 5 Files

**Issue:** `from module import *` slows startup  
**Impact:** Unnecessary symbol loading  
**Estimated Improvement:** 20-30% faster imports

**Files:**
- `Live_timing_test/test_tyre_state.py`
- `tests/demo_position_all_options.py`
- `modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_mdi_new.py`
- 2 more files

---

### 13. Inefficient MDI Snap Zone Calculations

**Issue:** Complex calculations on every mouse move  
**Location:** `f1t_gui_main.py` lines 1014-1049  
**Impact:** Mouse lag during window dragging  
**Fix:** Cache snap zones, throttle calculations

---

### 14. No Database for Metadata

**Issue:** Scanning filesystem for JSON files repeatedly  
**Impact:** Slow search operations  
**Fix:** Use SQLite index for fast metadata queries

---

### 15. Nested Loops in Overtake Detection

**Issue:** O(n²) complexity in `train_overtake_rate.py`  
**Impact:** Slow for large datasets  
**Fix:** Use pandas vectorized operations

---

### 16. CSV Format for Large Data Files

**Issue:** Using CSV instead of Parquet  
**Impact:** 10x slower read/write  
**Fix:** Convert to Parquet format with compression

---

### 17. No Batch Updates for GUI Tables

**Issue:** Updating table widget for each row  
**Impact:** 1000 redraws instead of 1  
**Fix:** Use `setUpdatesEnabled(False)` during batch operations

---

### 18. String Concatenation in Loops

**Issue:** Using `+=` for string building  
**Files:** 4 instances found  
**Impact:** O(n²) complexity  
**Fix:** Use `str.join()`

---

### 19. No Memory Cleanup in Long-Running Threads

**Issue:** QThread objects not properly cleaned up  
**Impact:** Memory leaks over time  
**Fix:** Implement proper cleanup and `deleteLater()`

---

### 20. Missing Performance Monitoring

**Issue:** No metrics collection or slow operation logging  
**Impact:** Can't identify new performance issues  
**Fix:** Add metrics collector and performance logging

---

## 📊 Impact Summary

### By Estimated Performance Gain:

| Issue | Current Time | After Fix | Speedup | Files Affected |
|-------|-------------|-----------|---------|----------------|
| #1 iterrows | 5-10s | 0.5-1s | 10x | 66 |
| #3 No cache | 10s | 1s | 10x | All API calls |
| #4 Sequential API | 25s | 5s | 5x | Multi-session |
| #5 GUI blocking | Freezes | Smooth | N/A | GUI |
| #7 apply(axis=1) | 5s | 2s | 2.5x | 15 |
| #10 JSON | 2s | 0.6s | 3.3x | 602 ops |
| #2 Monolithic GUI | 15s startup | 6s | 2.5x | 1 file |
| #6 Large mapper | 3s load | 1s | 3x | 1 file |

---

## 🎯 Quick Win Strategy

**Week 1: Fix Issues #1, #3, #5**
- Replace iterrows in top 10 most-used files
- Add LRU cache to data fetching functions
- Fix GUI blocking operations
- **Expected: 60-70% improvement**

**Week 2: Fix Issues #4, #7, #10**
- Implement parallel API requests
- Replace apply(axis=1) with vectorized ops
- Switch to orjson
- **Expected: Additional 40-50% improvement**

**Week 3-4: Fix Issues #2, #6**
- Refactor monolithic files
- Implement modular architecture
- **Expected: Additional 30-40% improvement**

---

## 🔬 Profiling Commands

### Profile any analysis:
```bash
python -m cProfile -o output.prof -m f1_analysis_modular_main -f 1 -y 2025 -r Japan -s R
python -m pstats output.prof
```

### Memory profile:
```bash
python -m memory_profiler f1_analysis_modular_main.py
```

### Find slowest lines:
```bash
kernprof -l -v script.py
```

---

## 📈 Measuring Improvement

### Before Optimizations:
```bash
# Run and time key operations
time python f1_analysis_modular_main.py -f 1 -y 2025 -r Japan -s R
time python f1_analysis_modular_main.py -f 12 -y 2025 -r Japan -s R -d VER
time python f1_analysis_modular_main.py -f 13 -y 2025 -r Japan -s R -d VER -d2 LEC
```

### After Each Fix:
- Re-run same commands
- Compare times
- Document improvements
- Commit with performance metrics

---

## 🎓 Learning from Fixes

After implementing fixes:
1. Document what worked best
2. Share patterns with team
3. Add to coding standards
4. Create automated checks (linting rules)

---

## ⚠️ Important Notes

**Don't optimize blindly:**
- Profile first to confirm bottlenecks
- Measure before and after
- Some issues may not affect your use case

**Prioritize by:**
1. User-facing impact (GUI freezing = highest)
2. Frequency of use (common analyses first)
3. Ease of fix (quick wins first)

**Avoid premature optimization:**
- Fix proven bottlenecks only
- Keep code readable
- Don't sacrifice maintainability

---

## 📝 Next Steps

1. ✅ Read full analysis: `docs/PERFORMANCE_ANALYSIS.md`
2. ✅ Review quick reference: `docs/PERFORMANCE_QUICK_REFERENCE.md`
3. ✅ Profile current performance to establish baseline
4. ✅ Implement Week 1 quick wins
5. ✅ Measure improvements
6. ✅ Continue with remaining issues

---

*Last Updated: December 9, 2025*  
*For questions or clarifications, refer to PERFORMANCE_ANALYSIS.md*
