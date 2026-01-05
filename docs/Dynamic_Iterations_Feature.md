# 动态迭代次数分配功能说明

**更新日期**: 2026-01-05  
**版本**: v2.0  
**状态**: ✅ 已实现并测试

---

## 📋 功能概述

实现了智能的动态迭代次数分配策略，根据车手的排位自动调整模拟计算量，同时确保用户选择的车手获得最精确的分析。

## 🎯 核心改进

### 1. 移除200次硬限制 ❌ → ✅

**之前**:
```python
# competitive_monte_carlo.py (旧版)
effective_iterations = min(iterations, 200)  # 强制限制
if iterations > 200:
    print(f"Reducing iterations from {iterations} to 200")
```

**现在**:
```python
# competitive_monte_carlo.py (新版)
effective_iterations = iterations  # 无限制
print(f"Running {effective_iterations} iterations (user-defined)")
```

用户现在可以设定任意迭代次数：500、1000、2000 等。

---

### 2. 动态迭代次数分配策略 🎮

根据车手排位智能分配计算资源：

| 排位范围 | 迭代次数比例 | 候选策略数 | 说明 |
|---------|------------|----------|------|
| **P1-P5** | 🔥 **100%** | 10个 | 前排车手，完整模拟 |
| **P6-P10** | ⚡ **50%** | 7个 | 中上游，平衡精度 |
| **P11-P20** | 💨 **30%** | 5个 | 中下游/后排，快速评估 |

**示例计算** (用户设定1000次):
- P3 车手: 1000次迭代 × 10个策略 = 全功率模拟
- P8 车手: 500次迭代 × 7个策略 = 中等精度
- P15车手: 300次迭代 × 5个策略 = 快速评估

---

### 3. 用户车手绝对优先 🏆

**三大保证**:

1. ✅ **100% 迭代次数**: 无论用户车手排位如何，始终使用用户设定的完整迭代次数
2. ✅ **最后模拟**: 在所有对手优化完成后才进行模拟，使用最准确的对手信息
3. ✅ **完整策略库**: 测试所有候选策略，不受排位限制

**Phase 1 - 对手优化**:
```
P1 (VER): 1000次 → P2 (NOR): 1000次 → ... → P20: 300次
[跳过用户车手 P8 (PER)]
```

**Phase 2 - 用户车手优化**:
```
P8 (PER): 1000次 [100%, 使用已知对手策略]
```

---

## 💻 代码实现位置

### 文件 1: `competitive_monte_carlo.py`
```python
# 行 248-253: 移除硬限制
iterations = self.mc_params.iterations
race_laps = self.sim_params.race_laps

# No hard limit - let user decide iteration count
effective_iterations = iterations
print(f"[COMPETITIVE_MC] Running {effective_iterations} iterations (user-defined)")
```

### 文件 2: `main_window.py` 
```python
# 行 1823-1842: Phase 1 动态分配
if driver_rank <= 5:
    opt_iterations = mc_iterations  # 100%
    opt_strategies = results[:10]
elif driver_rank <= 10:
    opt_iterations = int(mc_iterations * 0.5)  # 50%
    opt_strategies = results[:7]
else:
    opt_iterations = int(mc_iterations * 0.3)  # 30%
    opt_strategies = results[:5]

# 行 1880-1887: Phase 2 用户车手100%
print(f"[MAIN_WINDOW] 🎯 OUR DRIVER GETS 100% ITERATIONS: {mc_iterations}")
mc_params = MonteCarloParams(
    iterations=mc_iterations,  # ✅ Full iterations for our driver
    ...
)
```

---

## 📊 性能指南

### 推荐设置

| 使用场景 | 迭代次数 | 预计时间 | 精度 |
|---------|---------|---------|-----|
| 🚀 **快速测试** | 300-500 | 2-3分钟 | 中等 |
| ⚡ **日常使用** | 500-800 | 3-5分钟 | 良好 |
| 🎯 **精确分析** | 1000 | 5-8分钟 | 高 |
| 🔬 **专业研究** | 1500-2000 | 10-15分钟 | 极高 |

### 性能计算公式

```
总计算时间 ≈ (前排车手数 × 1.0 + 中游车手数 × 0.5 + 后排车手数 × 0.3) × 用户迭代次数 × 单次时间
```

**示例**: 
- 用户设定: 1000次
- 前排5人 (100%): 5 × 1000 = 5000次
- 中游5人 (50%): 5 × 500 = 2500次
- 后排9人 (30%): 9 × 300 = 2700次
- 用户车手 (100%): 1 × 1000 = 1000次
- **总计**: 11,200次迭代

---

## 🧪 测试验证

运行测试脚本:
```powershell
python test_dynamic_iterations.py
```

### 测试结果:
```
✅ TEST 1: 验证移除200次限制
   - 500次: PASS
   - 1000次: PASS
   - 1500次: PASS

✅ TEST 2: 验证动态迭代次数分配
   - P1-5 (100%): PASS
   - P6-10 (50%): PASS
   - P11-20 (30%): PASS

✅ TEST 3: 验证用户车手优先级
   - 最后模拟: PASS
   - 100%迭代: PASS
   - 已知对手策略: PASS
```

---

## 🔍 日志示例

### GUI 运行时日志:
```
======================================================================
[MAIN_WINDOW] ====== PHASE 1: Optimizing 19 opponent drivers ======
======================================================================

[PHASE_1] (1/19) Optimizing VER P1: Full MC (1000 iter, 100%)...
[PHASE_1] (2/19) Optimizing NOR P2: Full MC (1000 iter, 100%)...
[PHASE_1] (3/19) Optimizing HAM P6: Mid MC (500 iter, 50%)...
[PHASE_1] (4/19) Optimizing PER P8: Mid MC (500 iter, 50%)...
[PHASE_1] Skipping ALB (our driver, will optimize last)
[PHASE_1] (5/19) Optimizing STR P15: Quick MC (300 iter, 30%)...
...
[PHASE_1] ✅ Completed! 19 opponents optimized

======================================================================
[MAIN_WINDOW] ====== PHASE 2: Optimizing OUR driver (ALB) ======
[MAIN_WINDOW] Using 19 known opponent strategies
[MAIN_WINDOW] 🎯 OUR DRIVER GETS 100% ITERATIONS: 1000 (user-defined)
======================================================================

[COMPETITIVE_MC] Running 1000 iterations (user-defined)
[COMPETITIVE_MC] Running 1000 iterations x 5 strategies x 20 drivers...
```

---

## 🎨 GUI 界面更新

进度条显示:
```
Phase 1 (86%-90%): "Phase 1: VER P1 (Full MC 1000 iter, 100%)..."
Phase 2 (90%-95%): "Phase 2: 優化 ALB (100% 迭代)..."
```

---

## ⚠️ 注意事项

1. **计算时间**: 高迭代次数需要更长时间，建议使用进度条监控
2. **内存使用**: 1000次以上迭代可能消耗较多内存 (约2-3GB)
3. **结果精度**: 迭代次数越高，结果越稳定，但边际效益递减
4. **中断恢复**: 目前不支持中断后恢复，需重新运行

---

## 📝 更新记录

### v2.0 (2026-01-05)
- ✅ 移除200次硬限制
- ✅ 实现动态迭代次数分配 (100%/50%/30%)
- ✅ 确保用户车手100%迭代且最后模拟
- ✅ 添加详细日志输出
- ✅ 创建测试脚本验证功能

### v1.0 (2025-12-xx)
- 初始实现，固定200次上限

---

## 🚀 使用指南

1. **启动GUI**: `python strategy_simulator_main.py`
2. **设置迭代次数**: 在 Monte Carlo 设置中输入期望的次数 (建议500-1000)
3. **选择车手**: 选择您要分析的车手
4. **运行模拟**: 点击"执行 Monte Carlo"
5. **查看结果**: 在"位置分析"标签页查看结果

**提示**: 首次使用建议从500次开始，观察计算时间后再调整。

---

## 🤝 贡献者

- **开发**: F1T Team
- **测试**: User Feedback
- **文档**: AI Assistant

---

*此功能是 F1 Strategy Simulator 的核心改进，显著提升了分析的精度和灵活性。*
