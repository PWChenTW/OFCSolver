# 技術設計階段

執行DDD(領域驅動設計)技術設計，將需求轉換為具體的技術架構和實現方案。

## ⚠️ MVP 設計原則

在開始設計前，請記住：

### 第一版設計應該：
- **簡單直接**：使用最簡單的架構模式
- **快速實現**：選擇團隊熟悉的技術
- **專注核心**：只設計 MVP 需要的部分
- **延遲決策**：把複雜決策留到真正需要時

### 避免過度設計：
- ❌ 不要設計複雜的抽象層
- ❌ 不要預留過多的擴展點
- ❌ 不要使用不熟悉的設計模式
- ❌ 不要過早考慮性能優化

### 設計檢查清單：
- [ ] 這個設計能在一週內實現嗎？
- [ ] 團隊成員都理解這個設計嗎？
- [ ] 是否可以更簡單？
- [ ] 是否解決了核心問題？

## 用法
`/spec-design [功能名稱]`

## 功能說明

這個命令會：

1. **讀取需求文檔**
   - 分析BDD場景和驗收標準
   - 理解業務邏輯和約束條件
   - 識別技術挑戰點

2. **執行DDD設計** (強制委派給 architect)
   - **必須**委派給 `architect`，禁止主助手直接設計
   - 建立領域模型
   - 設計實體和值對象
   - 定義聚合邊界
   - 規劃領域服務
   - 遵循 MVP 原則，避免過度設計

3. **生成設計文檔**
   - 保存到 `.kiro/specs/[feature-name]/design.md`
   - 更新規格狀態為 `tasks`
   - 執行任務記錄：`python .claude/scripts/update_task_log.py`

## DDD設計流程

### 1. 領域分析
- 識別核心領域概念
- 建立通用語言
- 劃分限界上下文

### 2. 模型設計
- 定義實體(Entity)
- 設計值對象(Value Object)
- 確定聚合根(Aggregate Root)
- 規劃倉儲(Repository)

### 3. 架構設計
- 分層架構設計
- 依賴注入規劃
- 接口定義
- 數據流設計

### 4. 技術選型
- 框架和庫選擇
- 數據存儲方案
- API設計
- 集成方案

## 輸出格式

生成的 `design.md` 包含：

```markdown
# [功能名稱] 技術設計

## 領域模型

### 實體設計
```python
class User(Entity):
    """用戶聚合根"""
    def __init__(self, user_id: UserId, email: str):
        self.id = user_id
        self.email = email
        self.profile = UserProfile()
        self.roles = []
    
    def assign_role(self, role: Role) -> None:
        """分配角色"""
        pass
```

### 值對象設計
```python
@dataclass(frozen=True)
class UserProfile(ValueObject):
    """用戶資料值對象"""
    name: str
    avatar_url: Optional[str]
    created_at: datetime
    preferences: Dict[str, Any]
```

### 領域服務
```python
class AuthenticationService:
    """認證領域服務"""
    def authenticate(self, credentials: Credentials) -> AuthResult:
        pass
    
    def validate_token(self, token: str) -> Optional[User]:
        pass
```

## 架構設計

### 分層架構
```
Application Layer    # 應用服務、命令處理
     ↓
Domain Layer        # 實體、值對象、領域服務
     ↓
Infrastructure Layer # 倉儲實現、外部API
```

### 組件圖
```
[Auth Service] → [User Service] → [Permission Service]
        ↓              ↓                ↓
[Token Manager] → [Profile Manager] → [Role Manager]
```

## 技術規格

### API設計
- 用戶管理API：`/api/users`
- 認證API：`/api/auth`
- 權限檢查API：`/api/permissions`

### 數據模型
- 用戶表
- 角色權限表
- 認證記錄表

### 性能要求
- 認證響應時間：< 200ms
- 並發處理能力：5000 req/sec
- Token驗證速度：< 50ms

## 實施計劃

### 開發優先級
1. 核心領域模型
2. 認證流程
3. 權限管理
4. API接口
5. 測試覆蓋

### 技術風險
- [風險項目] → [緩解方案]
- [性能瓶頸] → [優化策略]

## 測試策略

### 單元測試
- 實體行為測試
- 值對象驗證
- 領域服務邏輯

### 集成測試
- API接口測試
- 數據庫集成測試
- 外部服務集成

### 端到端測試
- 完整業務流程測試
- 性能基準測試
```

## 設計原則

### DDD最佳實踐
1. **明確的領域邊界**：清晰的聚合邊界
2. **豐富的領域模型**：業務邏輯在領域層
3. **通用語言**：一致的術語使用
4. **依賴倒置**：領域層不依賴基礎設施

### 通用系統特殊考量
1. **安全性要求**：多層安全防護
2. **數據一致性**：事務邊界清晰
3. **可擴展性**：模組化設計
4. **審計追蹤**：完整的操作記錄

## 示例

```bash
> /spec-design user-auth
```

會基於用戶認證的需求分析，設計包含：
- User實體
- AuthenticationService領域服務
- UserProfile值對象
- UserRepository接口

## 質量檢查

設計完成後會自動檢查：
- [ ] 領域模型完整
- [ ] 架構分層清晰
- [ ] 接口定義明確
- [ ] 性能需求可達成
- [ ] 安全機制完善

## 人工審核點

在進入任務分解前，需要確認：
1. 架構設計合理
2. 技術選型適當
3. 性能指標可達成
4. 安全控制充分

通過審核後使用 `/spec-tasks [功能名稱]` 進入下一階段。