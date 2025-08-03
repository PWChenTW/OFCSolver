# /spec-implement - 實施階段管理

## 🚨 重要提醒：必須遵循 CLAUDE.md 原則

在執行此命令前，**必須**確保：
1. **核心開發原則**：遵循 MVP First、漸進式開發、批判性思考、實用主義
2. **AI 助手指導原則**：根據任務類型委派給適當的 Sub Agent（禁止直接實作）
3. **任務記錄要求**：完成任務後必須更新任務日誌

## 用途
進入功能的實施階段，協調開發工作並追蹤進度。

## 語法
```
/spec-implement <feature-name> [task-id]
```

## 參數
- `<feature-name>`: 功能名稱（必需）
- `[task-id]`: 特定任務ID（可選）- 直接開始特定任務

## 執行流程

### 1. 驗證前置條件
- 確認功能存在於 `.kiro/specs/`
- 檢查 `spec.json` 中的狀態
- 確認 tasks 階段已完成

### 2. 進入實施模式
如果未指定 task-id：
- 顯示所有任務清單和狀態
- 標記 spec 狀態為 "implementation"
- 建議開始順序

如果指定了 task-id：
- 直接開始該任務的實施
- 調用適當的 Sub Agent
- 更新任務狀態為 "in_progress"

### 3. 實施協調

#### 🔴 強制委派規則（必須遵守）
根據 CLAUDE.md 的指導原則，以下任務**必須**委派給相應的 Sub Agent：

- **架構與設計任務** → 委派給 `architect`
- **業務邏輯與需求** → 委派給 `business-analyst`
- **數據與算法** → 委派給 `data-specialist`
- **API 和集成** → 委派給 `integration-specialist`
- **測試與驗證** → 委派給 `test-engineer`
- **技術決策** → 委派給 `tech-lead`

**禁止**主助手直接實作任何程式碼！

#### 實施流程
- **自動調用適當的 Sub Agent**：
  - 根據任務類型自動匹配專家
  - 提供任務上下文和相關設計文檔
  - 確保 Sub Agent 了解核心開發原則
- **進度追蹤**：
  - 更新 `spec.json` 中的任務狀態
  - 記錄實施開始時間
- **品質檢查**：
  - 觸發相關的測試和檢查
  - 確保符合設計規範

### 4. 任務完成處理
- 更新任務狀態為 "completed"
- 執行相關測試
- **執行任務記錄**：
  ```bash
  python .claude/scripts/update_task_log.py
  ```
- 檢查是否所有任務都已完成
- 若全部完成，提示進入驗收階段

## 狀態管理
任務狀態流轉：
- `pending` → `in_progress` → `completed`
- 支援 `blocked` 狀態（遇到阻礙時）

## 範例

### 查看所有任務並進入實施模式
```
/spec-implement user-auth
```

### 直接開始特定任務
```
/spec-implement user-auth T001
```

## 輸出格式
```
📋 功能實施：[feature-name]

當前進度：
✅ T001: 建立用戶模型 [completed]
🔄 T002: 實現註冊API [in_progress]
⏳ T003: 實現登入API [pending]
⏳ T004: 實現JWT驗證 [pending]

整體進度：25% (1/4 完成)

建議：繼續實施 T002，預計需要 business-analyst 和 integration-specialist 協助。
```

## 相關命令
- `/spec-init` - 初始化新功能
- `/spec-tasks` - 查看或更新任務列表
- `/spec-status` - 查看功能狀態
- `/spec-complete` - 完成功能並進入驗收

## 注意事項
- 確保在開始實施前，設計階段已充分完成
- 每個任務應該獨立可驗證
- 遇到阻礙時及時更新狀態並記錄原因
- 保持與設計文檔的一致性
- **嚴格遵守委派規則**：主助手不得直接編寫程式碼
- **記住 MVP 原則**：從最簡單的實作開始
- **完成後必須記錄**：使用任務日誌系統記錄所有變更