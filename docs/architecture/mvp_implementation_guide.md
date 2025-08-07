# OFC Solver API - MVP 實作指南

## 🎯 MVP 目標

基於business-analyst的需求分析，實現核心功能的最簡可行版本：

### 核心功能
1. **基礎策略計算** - `POST /api/v1/analysis/calculate-strategy`
2. **簡化訓練系統** - `POST /api/v1/training/sessions`
3. **基礎遊戲管理** - `POST /api/v1/games/`

### 性能目標
- 即時計算 < 500ms
- 標準計算 < 5秒
- 支援 50+ 併發請求
- 99.5% 可用性

---

## 🏗️ 架構就緒狀態

### ✅ 已完成的架構組件

1. **中介軟體堆疊**
   - 錯誤處理中介軟體 (`ErrorHandlerMiddleware`)
   - 認證中介軟體 (`AuthenticationMiddleware`)
   - 頻率限制中介軟體 (`RateLimitMiddleware`)

2. **依賴注入系統**
   - 簡單容器實現 (`HandlerContainer`)
   - 資料庫會話管理 (`get_db_session`)
   - 處理器依賴注入 (`get_*_handler`)

3. **應用層處理器**
   - 遊戲處理器 (`GameCommandHandler`, `GameQueryHandler`)
   - 分析處理器 (`AnalysisCommandHandler`, `AnalysisQueryHandler`)
   - 訓練處理器 (`TrainingCommandHandler`, `TrainingQueryHandler`)

4. **統一錯誤處理**
   - 標準化錯誤響應格式
   - 領域異常映射
   - 環境相關的錯誤詳細程度

5. **安全架構**
   - API Key 認證 (MVP)
   - 公開端點配置
   - 基於用戶類型的頻率限制

---

## 🚀 MVP 實作階段

### Phase 1: 核心架構驗證 (1-2 天)

**目標**: 確保架構組件正常運作

**任務清單**:
- [ ] 啟動應用程式，確認所有中介軟體正常載入
- [ ] 測試錯誤處理中介軟體的各種異常情況
- [ ] 驗證 API Key 認證流程
- [ ] 測試頻率限制功能
- [ ] 確認依賴注入正常運作

**驗證方式**:
```bash
# 啟動應用程式
python src/main.py

# 測試基礎端點
curl http://localhost:8000/
curl http://localhost:8000/health

# 測試認證
curl -H "X-API-Key: ofc-solver-demo-key-2024" \
     http://localhost:8000/api/v1/games

# 測試頻率限制
# (多次快速請求同一端點)
```

### Phase 2: 核心業務邏輯實作 (3-5 天)

**目標**: 實作三個核心功能的基本版本

#### 2.1 基礎策略計算
```python
# 需要實作的組件
- PositionAnalyzer: 基本位置分析
- StrategyCalculator: 簡化策略計算
- CacheManager: 基本快取功能
```

#### 2.2 簡化訓練系統
```python
# 需要實作的組件  
- ScenarioGenerator: 隨機場景生成
- TrainingSession: 基本會話管理
- MoveEvaluator: 簡化評分系統
```

#### 2.3 基礎遊戲管理
```python
# 需要實作的組件
- GameEngine: 基本遊戲邏輯
- GameStateManager: 遊戲狀態管理
- PlayerManager: 玩家管理
```

### Phase 3: 整合測試與優化 (2-3 天)

**目標**: 確保系統整體穩定性

**任務清單**:
- [ ] 端到端功能測試
- [ ] 性能基準測試
- [ ] 錯誤處理測試
- [ ] 安全性驗證
- [ ] 文檔更新

---

## 🧪 測試策略

### 1. 架構層測試

**中介軟體測試**:
```python
# 測試錯誤處理
def test_error_handler_middleware():
    # 模擬各種異常
    # 驗證錯誤響應格式

# 測試認證
def test_authentication_middleware():
    # 測試有效/無效 API Key
    # 測試公開端點繞過
```

**依賴注入測試**:
```python  
def test_dependency_injection():
    # 測試處理器創建
    # 測試依賴解析
    # 測試生命週期管理
```

### 2. API 層測試

**功能端點測試**:
```python
def test_calculate_strategy_endpoint():
    # 測試不同計算模式
    # 驗證響應格式
    # 測試錯誤情況

def test_game_management_endpoints():
    # 測試遊戲CRUD操作
    # 驗證狀態轉換
```

### 3. 性能測試

**負載測試**:
```bash
# 使用 wrk 或 ab 進行負載測試
wrk -t12 -c50 -d30s --header "X-API-Key: test-key" \
    http://localhost:8000/api/v1/analysis/calculate-strategy
```

---

## 📋 檢查清單

### 部署前檢查

**功能檢查**:
- [ ] 所有核心端點正常響應
- [ ] 錯誤處理正確格式化
- [ ] 認證流程正常運作
- [ ] 頻率限制按預期執行
- [ ] 健康檢查端點可用

**性能檢查**:
- [ ] 即時計算 < 500ms
- [ ] 標準計算 < 5秒  
- [ ] 50併發請求正常處理
- [ ] 記憶體使用穩定

**安全檢查**:
- [ ] API Key 驗證正常
- [ ] 公開端點正確配置
- [ ] 錯誤信息不洩露敏感數據
- [ ] 輸入驗證充分

---

## 🔧 故障排除

### 常見問題

**1. 依賴注入失敗**
```python
# 錯誤: Handler not found
# 解決: 檢查 handlers/__init__.py 的導入
# 確認 dependencies.py 中的註冊邏輯
```

**2. 中介軟體順序問題**
```python
# 錯誤: Authentication bypassed
# 解決: 檢查 main.py 中的中介軟體添加順序
# 確保 AuthenticationMiddleware 在正確位置
```

**3. 資料庫連接問題**
```python
# 錯誤: Database session not initialized
# 解決: 檢查 lifespan 函數中的初始化順序
# 確認環境變數配置正確
```

---

## 📈 下一階段規劃

### Phase 4: 增強功能 (未來)

**優先級 1**:
- Redis 快取集成
- Celery 背景任務
- JWT 認證升級

**優先級 2**:
- 細粒度權限系統
- API 版本管理
- 監控和警報

**優先級 3**:
- 分布式追蹤
- 自動化部署
- 災難恢復

---

## 💡 關鍵設計決策

### 1. 簡單優於複雜
- 使用內存頻率限制而非 Redis (Phase 1)
- 硬編碼 API Key 而非資料庫查詢 (MVP)
- 簡單容器而非複雜 DI 框架

### 2. 可觀測性優先
- 所有請求都有唯一 ID
- 結構化錯誤響應
- 詳細的日誌記錄

### 3. 安全預設
- 預設拒絕存取
- 明確的公開端點列表
- 環境相關的錯誤詳細程度

### 4. 性能意識
- 異步處理優先
- 連接池預熱
- 適當的快取策略

---

## 🎉 成功指標

MVP 成功的標準：

1. **功能完整性**: 三個核心功能正常運作
2. **性能達標**: 滿足響應時間和併發要求
3. **穩定性**: 99.5% 可用性，無記憶體洩漏
4. **可維護性**: 清晰的程式碼結構，完整的測試覆蓋
5. **安全性**: 基本的認證和授權保護

達到這些標準後，架構就為下一階段的功能擴展做好了準備。