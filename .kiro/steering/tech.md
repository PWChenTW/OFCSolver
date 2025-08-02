# 技術架構

## 技術棧
- **後端**: Python 3.11+, FastAPI, Celery
- **前端**: React + TypeScript
- **數據庫**: PostgreSQL (主庫), Redis (緩存), ClickHouse (分析)
- **部署**: Docker, Kubernetes
- **求解器**: NumPy, SciPy (數學運算)

## 架構決策

### 核心架構
- **領域驅動設計 (DDD)**: 清晰的領域邊界和業務邏輯封裝
- **分層架構**: Domain, Application, Infrastructure, Presentation
- **CQRS**: 分離讀寫操作以優化性能
- **事件驅動**: 鬆耦合的領域事件系統

### 技術選型理由
1. **Python + FastAPI**: 非同步支持，適合計算密集型任務
2. **PostgreSQL + Redis**: 持久化存儲配合高速緩存
3. **Celery + RabbitMQ**: 處理長時間運行的求解計算
4. **Docker + K8s**: 彈性擴展和容器化部署

## 性能要求
- **策略計算**: 簡單局面 < 5秒，複雜局面 < 30秒
- **並發處理**: 支持 1000+ 同時計算
- **API 響應**: 95% 請求 < 200ms
- **系統可用性**: 99.5% uptime

## 已完成組件
- ✅ 基礎架構設置 (TASK-001)
- ✅ 數據庫配置 (TASK-002)
- ✅ 領域模型結構 (TASK-003)
- ✅ 牌和手牌模型 (TASK-004)
- ✅ 遊戲實體實現 (TASK-005)
- ✅ 手牌評估服務 (TASK-006)
