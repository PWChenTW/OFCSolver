# 支援多規則變體的架構方案

## 現狀分析

目前的架構已經有良好的分層和職責分離：
- `PineappleHandEvaluator` - 手牌評估
- `PineappleGameValidator` - 遊戲驗證
- `PineappleFantasyLandManager` - Fantasy Land 管理

## 簡單實用的解決方案

### 1. 配置驅動方法（推薦）

創建 `GameVariantConfig` 值對象來封裝不同平台的規則差異：

```python
# 使用範例
config = GameVariantConfig(
    variant_name="pineapple_ggpoker",
    fl_entry_requirement="QQ+",
    fl_stay_requirement="QQ+",  # 或其他規則
    royalty_middle={"flush": 8}  # 自定義評分
)

# 服務接受配置
evaluator = PineappleHandEvaluator(config)
fl_manager = PineappleFantasyLandManager(config)
```

### 2. 最小修改原則

只修改需要變化的部分：

```python
class PineappleFantasyLandManager:
    def __init__(self, config: GameVariantConfig = None):
        self.config = config or PINEAPPLE_STANDARD
        
    def check_stay_qualification(self, top, middle, bottom):
        if self.config.fl_stay_requirement == "QQ+":
            return self.check_entry_qualification(top)
        elif self.config.fl_stay_requirement == "trips_top_or_fh_middle_or_quads_bottom":
            # 原有的複雜規則
            return self._check_complex_stay_rules(top, middle, bottom)
```

### 3. 避免過度設計

**不需要**：
- 複雜的策略模式
- 抽象工廠
- 過多的繼承層次

**只需要**：
- 簡單的配置對象
- 條件判斷
- 清晰的命名

## 實施步驟

### 第一階段（1-2天）
1. 創建 `GameVariantConfig` 類
2. 修改 `PineappleFantasyLandManager` 支援配置
3. 測試現有功能不受影響

### 第二階段（2-3天）
1. 收集不同平台的具體規則差異
2. 創建預定義的配置常量
3. 修改其他服務支援配置

### 第三階段（需要時）
1. 根據實際需求擴展配置選項
2. 添加配置驗證
3. 考慮配置的持久化

## 批判性思考

1. **真的需要支援很多變體嗎？**
   - 先支援 2-3 個主流平台
   - 其他的等有需求再加

2. **規則差異有多大？**
   - 大部分差異集中在 Fantasy Land 和評分
   - 核心遊戲邏輯相同

3. **訓練 Solver 的影響**
   - 不同規則需要不同的訓練
   - 但代碼架構可以共用

## 結論

使用簡單的配置驅動方法，避免過度工程。當前架構已經足夠靈活，只需要小幅調整即可支援多種規則變體。