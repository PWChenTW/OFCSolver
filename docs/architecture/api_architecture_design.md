# OFC Solver API 架構設計

## 概述

本文檔描述了 OFC Solver System REST API 的完整架構設計，基於 MVP 優先原則，提供了一個簡單、可擴展、可維護的解決方案。

## 架構原則

### MVP 優先 (MVP First)
- 從最簡單的可運行版本開始
- 避免過度設計，專注核心功能
- 快速驗證架構決策的有效性

### 漸進式架構 (Progressive Architecture)
- 支持功能的逐步擴展
- 明確的升級路徑
- 向後相容性考慮

### 實用主義 (Pragmatism)
- 平衡技術理想與現實約束
- 優先考慮業務價值
- 可操作性勝過完美性

---

## 整體架構

```
┌─────────────────────────────────────────────┐
│              Client Applications             │
└─────────────────┬───────────────────────────┘
                  │ HTTP/HTTPS
┌─────────────────┴───────────────────────────┐
│            FastAPI Web Layer                │
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────┐ │
│  │        Middleware Stack                 │ │
│  │  1. CORS                               │ │
│  │  2. GZip Compression                   │ │
│  │  3. Error Handling                     │ │
│  │  4. Rate Limiting                      │ │
│  │  5. Authentication                     │ │
│  └─────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────┐ │
│  │          API Controllers                │ │
│  │  • Game Controller                     │ │
│  │  • Analysis Controller                 │ │
│  │  • Training Controller                 │ │
│  │  • Health Controller                   │ │
│  └─────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────┘
                  │ Dependency Injection
┌─────────────────┴───────────────────────────┐
│            Application Layer                │
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────┐ │
│  │        Command Handlers                 │ │
│  │  • GameCommandHandler                  │ │
│  │  • AnalysisCommandHandler              │ │
│  │  • TrainingCommandHandler              │ │
│  └─────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────┐ │
│  │         Query Handlers                  │ │
│  │  • GameQueryHandler                    │ │
│  │  • AnalysisQueryHandler                │ │
│  │  • TrainingQueryHandler                │ │
│  └─────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────┴───────────────────────────┐
│             Domain Layer                    │
├─────────────────────────────────────────────┤
│  • Entities     • Value Objects            │
│  • Services     • Repository Interfaces    │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────┴───────────────────────────┐
│          Infrastructure Layer               │
├─────────────────────────────────────────────┤
│  ┌─────────────┬─────────────┬─────────────┐ │
│  │  Database   │   Cache     │ Background  │ │
│  │ (PostgreSQL)│  (Redis)    │   Tasks     │ │
│  │             │             │  (Celery)   │ │
│  └─────────────┴─────────────┴─────────────┘ │
└─────────────────────────────────────────────┘
```

---

## 中介軟體堆疊

### 中介軟體執行順序
中介軟體的執行順序對系統行為至關重要：

1. **CORS Middleware** - 處理跨域請求
2. **GZip Middleware** - 響應壓縮
3. **Error Handler Middleware** - 統一錯誤處理
4. **Rate Limiting Middleware** - 請求頻率控制
5. **Authentication Middleware** - 用戶認證

### 1. 錯誤處理中介軟體

**功能**：
- 統一錯誤響應格式
- 領域異常到 HTTP 狀態碼映射
- 環境相關的錯誤詳細程度
- 請求追蹤和日誌記錄

**MVP 特性**：
```python
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "timestamp": "2024-01-01T00:00:00Z",
    "path": "/api/v1/games",
    "method": "POST",
    "request_id": "req-123"
  }
}
```

### 2. 認證中介軟體

**認證方式**：
- **API Key** (MVP): 簡單的基於 header 的認證
- **JWT** (Phase 2): 完整的 token 基認證

**公開端點**：
- 健康檢查 (`/health`)
- API 文檔 (`/api/docs`, `/api/redoc`)
- 基礎策略計算 (`/api/v1/analysis/calculate-strategy`)
- 隨機訓練場景 (`/api/v1/training/scenarios/random`)

**MVP API Keys**：
```
Demo User: ofc-solver-demo-key-2024
Test User: ofc-solver-test-key-2024
```

### 3. 頻率限制中介軟體

**限制策略**：
- 基於用戶類型的不同限制
- 端點特定的倍數調整
- 滑動時間窗口 (1分鐘)

**用戶類型限制**：
- Anonymous: 30 requests/min
- Demo: 100 requests/min
- Test: 1000 requests/min

**端點調整**：
- Analysis endpoints: 0.5x (計算密集)
- Game queries: 2.0x (輕量級)
- Training: 1.5x (中等)

---

## 依賴注入架構

### MVP 依賴容器

**設計原則**：
- 簡單的容器實現，避免複雜的 DI 框架
- 明確的生命週期管理
- 易於測試的依賴替換

**核心依賴**：
```python
# Database session
async def get_db_session() -> AsyncSession

# Application handlers  
async def get_game_command_handler() -> GameCommandHandler
async def get_analysis_query_handler() -> AnalysisQueryHandler

# Authentication
async def get_current_user() -> Dict[str, Any]
async def require_authentication() -> Dict[str, Any]
```

### 生命週期管理

**Singleton**：
- 配置設定 (`Settings`)
- 資料庫連接池 (`ConnectionPool`)
- 快取客戶端 (`RedisClient`)

**Scoped**：
- 資料庫會話 (`AsyncSession`)
- 用戶上下文 (`UserContext`)

**Transient**：
- 命令/查詢處理器
- DTO 和驗證器

---

## 錯誤處理策略

### 異常映射

| 領域異常 | HTTP 狀態碼 | 錯誤代碼 |
|---------|------------|---------|
| `ValidationError` | 400 | `VALIDATION_ERROR` |
| `GameNotFoundError` | 404 | `GAME_NOT_FOUND` |
| `InvalidGameStateError` | 409 | `INVALID_GAME_STATE` |
| `CalculationTimeoutError` | 408 | `CALCULATION_TIMEOUT` |
| `AuthenticationError` | 401 | `AUTHENTICATION_FAILED` |
| `RateLimitExceededError` | 429 | `RATE_LIMIT_EXCEEDED` |

### 錯誤響應格式

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "timestamp": "2024-01-01T00:00:00Z",
    "path": "/api/endpoint",
    "method": "POST",
    "request_id": "uuid",
    "trace": "stack trace (dev only)"
  }
}
```

---

## 性能優化架構

### 1. 快取策略

**Redis 集成**：
- 策略計算結果快取
- 會話狀態快取
- 頻率限制數據

**快取模式**：
- **Cache-Aside**: 主動快取管理
- **TTL**: 基於時間的過期
- **LRU**: 記憶體不足時的清理

### 2. 異步處理

**背景任務**：
- 長時間的策略計算
- 批次分析處理
- 報告生成

**Celery 集成**：
```python
# 長時間計算的異步處理
@celery.task
async def calculate_exhaustive_strategy(position_data):
    # 執行複雜計算
    return strategy_result
```

### 3. 資料庫優化

**連接池配置**：
- 最小連接數: 5
- 最大連接數: 20
- 連接超時: 30 秒
- 健康檢查: 啟用

**查詢優化**：
- 準備語句快取
- 連接池預熱
- 異步查詢處理

---

## 安全防護架構

### 1. 認證與授權

**認證流程**：
1. 提取 API Key 或 JWT Token
2. 驗證 Token 有效性
3. 載入用戶信息和權限
4. 設置請求上下文

**授權檢查**：
- 端點級別權限控制
- 功能特性訪問控制
- 資源級別權限檢查

### 2. 輸入驗證

**驗證層級**：
1. **HTTP 層**: Content-Type, 請求大小
2. **Pydantic 層**: 數據類型和格式驗證  
3. **業務層**: 業務規則驗證
4. **領域層**: 領域約束驗證

### 3. 安全標頭

```python
# 自動添加的安全標頭
{
    "X-Request-ID": "unique-request-id",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block"
}
```

---

## MVP 實作建議

### Phase 1: 核心架構 (MVP)

**優先實作**：
1. ✅ 基礎中介軟體堆疊
2. ✅ 簡單依賴注入容器
3. ✅ 統一錯誤處理
4. ✅ API Key 認證
5. ✅ 內存頻率限制

**延後實作**：
- JWT 認證
- Redis 快取集成
- 複雜的權限系統
- 監控和觀測性

### Phase 2: 性能優化

**要實作的功能**：
- Redis 快取集成
- Celery 背景任務
- 資料庫查詢優化
- API 響應快取

### Phase 3: 企業級功能

**要實作的功能**：
- JWT 認證和刷新機制
- 細粒度權限系統
- 審計日誌
- 監控和警報
- API 版本管理

---

## 測試策略

### 1. 單元測試

**覆蓋範圍**：
- 中介軟體邏輯
- 錯誤處理器
- 認證邏輯
- 依賴注入容器

### 2. 集成測試

**測試場景**：
- 完整的請求/響應流程
- 認證和授權流程
- 錯誤處理流程
- 頻率限制行為

### 3. 性能測試

**測試指標**：
- 響應時間 (< 500ms for instant, < 5s for standard)
- 併發處理能力 (50+ requests)
- 記憶體使用量
- 快取命中率

---

## 部署考慮

### 1. 容器化

**Docker 配置**：
- 多階段構建優化映像大小
- 健康檢查端點集成
- 環境特定配置

### 2. 橫向擴展

**無狀態設計**：
- 會話狀態存儲在 Redis
- 文件上傳使用對象存儲
- 背景任務通過隊列處理

### 3. 監控

**觀測性**：
- 結構化日誌
- 指標收集 (Prometheus)
- 分布式追蹤 (Jaeger)
- 健康檢查端點

---

## 總結

本架構設計基於 MVP 優先原則，提供了：

1. **簡單但完整**的中介軟體堆疊
2. **可擴展**的依賴注入架構
3. **統一**的錯誤處理策略
4. **分層**的安全防護
5. **漸進式**的升級路徑

這個架構支持快速開發和部署，同時為未來的擴展提供了堅實的基礎。通過明確的階段劃分，團隊可以專注於當前的 MVP 目標，同時為長期發展做好準備。