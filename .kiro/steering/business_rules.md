# Business Rules

## OFC 遊戲變體

### Pineapple OFC (主要變體)
基於 `/docs/rules/OFC_GAME_RULES.md` 的規則：

#### 發牌機制
- Street 0: 發5張，全部擺放
- Streets 1-4: 發3張，選2張擺放，棄1張

#### Fantasy Land 策略重要性
1. **進入條件**：前墩 QQ+ (比 Standard OFC 的 AA+ 容易)
2. **策略核心**：
   - 進入 Fantasy Land 是最高優先級目標
   - 在 Fantasy Land 中更容易維持（滾雪球效應）
   - 一次看到所有牌，可完美規劃佈局

#### 獎勵分數差異
- 中墩獎勵分數較高（如同花 8 分 vs 4 分）
- 前墩三條從 10 分開始遞增
- 詳見 `/docs/rules/OFC_GAME_RULES.md`

#### 特殊規則
- 支援鬼牌（Joker）作為萬能牌
- 犯規懲罰嚴重，需謹慎平衡風險

### 評分系統可變性
- 評分系統預期會持續調整
- 需要支援多版本評分配置
- 訓練模型時需考慮評分系統對策略的影響