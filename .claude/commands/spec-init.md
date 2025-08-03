# 初始化功能規格

## 🚨 重要：遵循 CLAUDE.md 核心開發原則

初始化功能時必須遵循：
- **MVP First**：從最簡單的版本開始
- **漸進式開發**：一次只加一個小功能
- **批判性思考**：質疑需求的必要性
- **實用主義**：避免過度設計

初始化一個新的功能規格，創建SDD(規格驅動開發)流程的起始點。

## 用法
`/spec-init [功能名稱] [簡短描述]`

## 功能說明

這個命令會自動：

1. **創建規格目錄結構**
   ```
   .kiro/specs/[feature-name]/
   ├── spec.json          # 規格狀態追蹤
   ├── requirements.md    # BDD需求文檔（待生成）
   ├── design.md         # DDD設計文檔（待生成）
   └── tasks.md          # 任務清單（待生成）
   ```

2. **設置規格狀態**
   - 狀態：`requirements` (等待需求分析)
   - 創建時間戳
   - 功能基本信息

3. **觸發需求分析階段**
   - 自動調用 `business-analyst` 進行BDD需求分析
   - 或提示進入下一階段

## 示例

```bash
> /spec-init user-auth "實現用戶認證和授權系統"
```

這將創建：
- 目錄：`.kiro/specs/user-auth/`
- 狀態：等待BDD需求分析
- 下一步：使用 `/spec-requirements user-auth` 進行需求分析

## 規格狀態流程

```
init → requirements → design → tasks → implementation → completed
```

每個階段都需要人工審核確認才能進入下一階段，確保品質和正確性。

## 模板變量

創建規格時可以使用以下變量：
- `{feature_name}`: 功能名稱
- `{description}`: 功能描述
- `{timestamp}`: 創建時間
- `{author}`: 創建者（如果可獲得）

## 注意事項

1. **命名規範**：功能名稱使用小寫字母和連字符
2. **唯一性檢查**：避免重複的功能名稱
3. **描述清晰**：提供清楚的功能描述有助於後續分析
4. **階段順序**：必須按照SDD流程順序進行