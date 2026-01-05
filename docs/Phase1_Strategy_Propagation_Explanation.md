# Phase 1 策略传播机制说明

**问题**: 每一位车手会因为前面车手模拟的结果而改变策略吗？

**答案**: ✅ **是的！这正是 Phase 1 的核心设计逻辑。**

---

## 📊 工作原理

### 逐步策略传播

在 Phase 1 中，系统按照**起跑排位顺序**依次优化每位对手车手，后面的车手会使用前面车手已经确定的最佳策略进行模拟。

```
opponent_best_strategies = {}  # 开始时为空

车手 1 (P1 VER):
  ├─ 输入: opponent_strategies = {}  (无已知策略)
  ├─ 模拟: 测试 10 个候选策略
  └─ 输出: VER 最佳策略 → M-H (70% 胜率)
        ↓
        opponent_best_strategies['VER'] = {'tire_sequence': ['M', 'H'], ...}

车手 2 (P2 NOR):
  ├─ 输入: opponent_strategies = {'VER': M-H}  ✅ 使用 VER 的策略
  ├─ 模拟: 测试 10 个候选策略，考虑 VER 会用 M-H
  └─ 输出: NOR 最佳策略 → S-H (65% 胜率)
        ↓
        opponent_best_strategies['NOR'] = {'tire_sequence': ['S', 'H'], ...}

车手 3 (P3 LEC):
  ├─ 输入: opponent_strategies = {'VER': M-H, 'NOR': S-H}  ✅ 使用前两者策略
  ├─ 模拟: 测试 10 个候选策略，考虑 VER 和 NOR 的策略
  └─ 输出: LEC 最佳策略 → M-M-H (62% 胜率)
        ↓
        opponent_best_strategies['LEC'] = {'tire_sequence': ['M', 'M', 'H'], ...}

... (继续到 P20)

车手 20 (P20 SAR):
  ├─ 输入: opponent_strategies = {所有前19位车手的策略}  ✅ 完整信息
  ├─ 模拟: 测试 5 个候选策略，考虑所有前面车手的策略
  └─ 输出: SAR 最佳策略 → H-M (35% 得分率)
```

---

## 🔍 代码证据

### 1. Phase 1 调用 (main_window.py:1856-1863)

```python
# Run quick MC for this driver
best_strategy = self._quick_mc_for_driver(
    driver_code=driver_code,
    grid_position=driver_rank,
    candidate_strategies=opt_strategies,
    iterations=opt_iterations,
    sim_params=sim_params,
    fp2_predictions=fp2_predictions,
    opponent_strategies=opponent_best_strategies,  # ✅ 传递已知策略
    long_run_data=long_run_data,
)

opponent_best_strategies[driver_code] = best_strategy  # ✅ 存储结果
```

**关键点**: 
- `opponent_strategies=opponent_best_strategies` - 传递前面车手的策略
- `opponent_best_strategies[driver_code] = best_strategy` - 立即更新字典

### 2. CompetitiveMonteCarloSimulator 初始化 (competitive_monte_carlo.py:189-203)

```python
def __init__(
    self,
    sim_params: SimulationParams,
    mc_params: MonteCarloParams,
    fp2_predictions: List[Dict],
    opponent_strategies: Optional[Dict[str, Dict]] = None,  # ✅ 接收对手策略
    long_run_data: Optional[Dict] = None,
):
    self.opponent_strategies = opponent_strategies or {}  # ✅ 存储
```

### 3. 单次迭代使用对手策略 (competitive_monte_carlo.py:316)

```python
def _run_single_iteration(self, ...):
    simulator = FullRaceSimulator(...)
    simulator.load_drivers(self.fp2_predictions, self.long_run_data)
    
    # ✅ 设置对手策略 (前面车手已确定的策略)
    simulator.set_opponent_strategies(self.opponent_strategies)
    
    # 设置当前正在测试的车手策略
    simulator.set_our_strategy(self._our_driver, strategy.stints)
```

### 4. FullRaceSimulator 应用策略 (race_simulator.py:266-292)

```python
def set_opponent_strategies(self, opponent_settings: Dict[str, Dict]):
    """将已知的对手策略应用到模拟中"""
    for driver_code, settings in opponent_settings.items():
        if driver_code not in self._drivers:
            continue
        
        tire_sequence = settings.get('tire_sequence', ['M', 'H'])
        stints = self._create_stints_from_sequence(tire_sequence, driver_code)
        self._strategies[driver_code] = stints  # ✅ 设置该车手的策略
        
        # 设置初始轮胎
        self._drivers[driver_code].stints = stints
        self._drivers[driver_code].current_tire = stints[0].compound
```

---

## 💡 为什么这样设计？

### 优势

1. **更真实的模拟**
   - 后排车手知道前排会用什么策略
   - 可以选择"跟随"或"差异化"策略

2. **避免策略冲突**
   - 如果所有车手独立优化，可能所有人都选同一策略
   - 渐进式优化让每个车手考虑已有信息

3. **效率提升**
   - 不需要多轮迭代寻找纳什均衡
   - 单次遍历即可得到合理的策略分配

### 实际影响示例

**场景**: 摩纳哥赛道 (超车困难)

```
P1 VER 优化:
  - 测试 S-M-H, M-H, S-H
  - 最佳: S-M-H (因为可以利用 undercut)
  - 结果: S-M-H

P2 LEC 优化 (知道 VER 用 S-M-H):
  - 测试 S-M-H, M-H, S-H
  - 发现: S-M-H 会被 VER 挡在后面
  - 发现: M-H 可以在 VER 第一次进站时超越
  - 最佳: M-H (差异化策略)
  - 结果: M-H

P3 SAI 优化 (知道 VER 用 S-M-H, LEC 用 M-H):
  - 测试各种策略
  - 发现: S-M-H 和 M-H 都有车手在用
  - 最佳: H-M (one-stop，赌安全车)
  - 结果: H-M
```

---

## 🎯 与 Phase 2 的区别

### Phase 1 (对手优化)
```
目标: 为每个对手找到最佳策略
方法: 渐进式优化，后面的车手使用前面的结果
```

### Phase 2 (用户车手优化)
```
目标: 为用户车手找到最佳策略
方法: 使用所有 19 个对手的已知策略进行模拟
优势: 最精确的分析 (100% 迭代次数 + 完整对手信息)
```

---

## 📊 数据流图

```
[Phase 1 开始]
    ↓
opponent_best_strategies = {}
    ↓
┌─────────────────────────────────────────┐
│ 按排位顺序遍历 (P1 → P20)                │
├─────────────────────────────────────────┤
│ 当前车手: P{n}                           │
│   ├─ 跳过用户车手                        │
│   ├─ 调用 _quick_mc_for_driver()        │
│   │   └─ 传入 opponent_strategies       │
│   │       (包含 P1 到 P{n-1} 的策略)     │
│   ├─ CompetitiveMonteCarloSimulator     │
│   │   ├─ 存储 opponent_strategies        │
│   │   └─ 每次迭代使用这些策略            │
│   ├─ FullRaceSimulator                  │
│   │   └─ set_opponent_strategies()      │
│   │       (实际应用到 20 车手模拟)       │
│   └─ 返回最佳策略                        │
│       ↓                                  │
│   opponent_best_strategies[P{n}] = 结果 │ ✅ 立即更新
└─────────────────────────────────────────┘
    ↓
[Phase 1 完成] 所有 19 个对手策略已确定
    ↓
[Phase 2 开始] 用户车手使用所有 19 个策略
```

---

## ✅ 总结

**问题**: 每一位车手会因为前面车手模拟的结果而改变策略吗？

**答案**: 
- ✅ **是的**，这是核心设计
- 后面的车手会看到前面车手的策略
- 他们的最佳策略会受到影响
- 这让模拟更接近现实 (车队之间互相观察和反应)

**关键代码位置**:
1. `main_window.py:1863` - 传递 `opponent_best_strategies`
2. `main_window.py:1867` - 立即更新字典
3. `competitive_monte_carlo.py:316` - 应用到模拟器
4. `race_simulator.py:266` - 实际设置对手策略

这就是为什么 Phase 1 按排位顺序处理，而不是并行处理所有车手！
