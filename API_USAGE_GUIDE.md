# OFC Solver API 使用指南

## 概述

基於 MVP 原則實現的 OFC Solver REST API，提供策略計算、訓練管理、遊戲狀態管理等核心功能。

## 快速開始

### 1. 啟動服務

```bash
# 開發環境
python src/main.py

# 或使用 uvicorn
uvicorn src.main:create_app --reload --host 0.0.0.0 --port 8000
```

### 2. 查看 API 文檔

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

### 3. 健康檢查

```bash
curl http://localhost:8000/health
```

## 認證說明

### API Key 認證（MVP）

**方式一：Authorization Header（推薦）**
```bash
curl -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
     http://localhost:8000/api/v1/analysis/sessions/{session_id}
```

**方式二：X-API-Key Header**
```bash
curl -H "X-API-Key: ofc-solver-demo-key-2024" \
     http://localhost:8000/api/v1/training/sessions
```

**方式三：查詢參數（僅開發環境）**
```bash
curl "http://localhost:8000/api/v1/games?api_key=ofc-solver-demo-key-2024"
```

### 可用的 API Keys

- `ofc-solver-demo-key-2024` - 演示用戶（基礎功能）
- `ofc-solver-test-key-2024` - 測試用戶（所有功能）

## 核心 API 端點

### 🎯 分析服務 (Analysis)

#### 1. 計算策略（核心功能）- 公開端點

```bash
curl -X POST http://localhost:8000/api/v1/analysis/calculate-strategy \
  -H "Content-Type: application/json" \
  -d '{
    "position": {
      "players_hands": {
        "player_1": {
          "front": ["As", "Kh"],
          "middle": ["Qd", "Jc", "10s"],
          "back": ["9h", "8d", "7c", "6s", "5h"]
        }
      },
      "remaining_cards": ["2h", "3c", "4d", "Ts"],
      "current_player": 0,
      "round_number": 2
    },
    "calculation_mode": "standard",
    "max_calculation_time_seconds": 30
  }'
```

**響應示例：**
```json
{
  "success": true,
  "data": {
    "session_id": "abc-123-def",
    "strategy": {
      "recommended_action": "place_card",
      "card": "2h",
      "position": "middle",
      "reasoning": "Optimal placement based on standard analysis"
    },
    "expected_value": 2.5,
    "confidence": 0.95,
    "calculation_method": "standard",
    "calculation_time_ms": 2500,
    "alternative_moves": [
      {
        "action": "place_front",
        "expected_value": 2.1,
        "confidence": 0.85
      }
    ]
  },
  "message": "Strategy calculated successfully"
}
```

#### 2. 獲取分析歷史 - 需要認證

```bash
curl -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
     "http://localhost:8000/api/v1/analysis/history?limit=10&offset=0"
```

#### 3. 策略比較 - 需要高級功能

```bash
curl -X POST http://localhost:8000/api/v1/analysis/compare-strategies \
  -H "Authorization: ApiKey ofc-solver-test-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "positions": [
      {
        "players_hands": {"player_1": {"front": ["As", "Kh"], "middle": [], "back": []}},
        "remaining_cards": ["2h", "3c"],
        "current_player": 0,
        "round_number": 1
      },
      {
        "players_hands": {"player_1": {"front": ["Ac", "Kd"], "middle": [], "back": []}},
        "remaining_cards": ["2h", "3c"],
        "current_player": 0,
        "round_number": 1
      }
    ],
    "comparison_metrics": ["expected_value", "confidence"]
  }'
```

### 🎓 訓練服務 (Training)

#### 1. 開始訓練會話 - 需要認證

```bash
curl -X POST http://localhost:8000/api/v1/training/sessions \
  -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "550e8400-e29b-41d4-a716-446655440000",
    "difficulty": "medium",
    "max_exercises": 10,
    "training_mode": "guided"
  }'
```

#### 2. 獲取訓練會話詳情 - 需要認證

```bash
curl -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
     "http://localhost:8000/api/v1/training/sessions/550e8400-e29b-41d4-a716-446655440000?include_exercises=true"
```

#### 3. 提交練習答案 - 需要認證

```bash
curl -X POST http://localhost:8000/api/v1/training/sessions/550e8400-e29b-41d4-a716-446655440000/submit-answer \
  -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_id": "660e8400-e29b-41d4-a716-446655440001",
    "user_action": "middle",
    "time_taken_seconds": 25.5,
    "used_hints": 0
  }'
```

#### 4. 獲取用戶進度 - 需要認證

```bash
curl -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
     "http://localhost:8000/api/v1/training/progress/demo_user?days_back=30"
```

#### 5. 查看排行榜 - 需要認證

```bash
curl -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
     "http://localhost:8000/api/v1/training/leaderboard?leaderboard_type=weekly&limit=10"
```

### 🎮 遊戲服務 (Games)

#### 1. 創建遊戲 - 需要認證

```bash
curl -X POST http://localhost:8000/api/v1/games/ \
  -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "player_count": 2,
    "rules_variant": "standard",
    "game_mode": "casual",
    "fantasy_land_enabled": true
  }'
```

#### 2. 獲取遊戲狀態 - 需要認證

```bash
curl -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
     "http://localhost:8000/api/v1/games/550e8400-e29b-41d4-a716-446655440000"
```

#### 3. 獲取遊戲詳細狀態 - 需要認證

```bash
curl -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
     "http://localhost:8000/api/v1/games/550e8400-e29b-41d4-a716-446655440000/state"
```

#### 4. 放置卡牌 - 需要認證

```bash
curl -X POST http://localhost:8000/api/v1/games/550e8400-e29b-41d4-a716-446655440000/place-card \
  -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "card": "As",
    "position": "middle_1"
  }'
```

#### 5. 遊戲動作 - 需要認證

```bash
curl -X POST http://localhost:8000/api/v1/games/550e8400-e29b-41d4-a716-446655440000/action \
  -H "Authorization: ApiKey ofc-solver-demo-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "ready"
  }'
```

## 錯誤處理

### 標準錯誤響應格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "timestamp": "2024-01-01T12:00:00Z",
    "path": "/api/v1/analysis/calculate-strategy",
    "method": "POST",
    "request_id": "req-abc-123"
  }
}
```

### 常見錯誤碼

- `VALIDATION_ERROR` (400) - 輸入驗證失敗
- `AUTHENTICATION_FAILED` (401) - 認證失敗
- `ACCESS_DENIED` (403) - 權限不足
- `NOT_FOUND` (404) - 資源不存在
- `RATE_LIMIT_EXCEEDED` (429) - 請求頻率超限
- `INTERNAL_SERVER_ERROR` (500) - 服務器內部錯誤

## 性能和限制

### 請求限制

- **API Key 認證用戶**：
  - Demo用戶：100 請求/分鐘
  - Test用戶：1000 請求/分鐘
- **分頁限制**：最大 100 項/頁
- **策略計算**：
  - Instant模式：5秒超時
  - Standard模式：30秒超時
  - Exhaustive模式：120秒超時

### 響應時間目標

- **即時計算** < 500ms
- **標準計算** < 5秒
- **查詢操作** < 1秒
- **批量操作** < 10秒

## 開發和測試

### 運行測試腳本

```bash
# 基本功能測試
python test_api_basic.py

# 完整測試套件
python -m pytest tests/
```

### 本地開發設置

```bash
# 安裝依賴
pip install -r requirements.txt

# 運行開發服務器
python src/main.py

# 查看日誌
tail -f logs/app.log
```

## 未來發展

### 第二階段功能
- JWT 認證支持
- WebSocket 實時遊戲
- 高級統計分析
- 機器學習推薦

### 第三階段功能
- 錦標賽系統
- 社交功能
- 移動端 API
- 高級可視化

## 技術支持

- **問題回報**：GitHub Issues
- **API文檔**：http://localhost:8000/api/docs
- **健康監控**：http://localhost:8000/health

---

此 API 基於 MVP 原則實現，專注於核心功能的快速驗證和迭代開發。