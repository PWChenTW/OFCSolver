# Git 工作流程指南

## 📋 概述

本文檔定義了AI協作開發項目的Git工作流程，確保多實例協作的代碼管理井然有序。

## 🌳 分支策略

### 主要分支結構

```
main (穩定版本)
├── develop (開發集成)
├── feature/[功能名稱] (功能開發)
├── role/[角色名稱] (角色專用)
├── hotfix/[修復名稱] (緊急修復)
└── release/[版本號] (發版準備)
```

### 分支命名規範

#### 功能分支 (Feature Branches)
```bash
# 格式: feature/[spec-name]-[簡短描述]
feature/user-auth-login          # 用戶登錄功能
feature/api-rest-endpoints       # REST API端點
feature/ui-dashboard            # 儀表板界面
feature/data-processing         # 數據處理邏輯
```

#### 角色分支 (Role Branches)  
```bash
# 格式: role/[agent-name]-[時間戳]
role/business-analyst-20240127   # 業務分析師專用分支
role/architect-20240127         # 架構師專用分支
role/test-engineer-20240127     # 測試工程師專用分支
```

#### 修復分支 (Hotfix Branches)
```bash
# 格式: hotfix/[問題描述]
hotfix/login-security-fix       # 登錄安全修復
hotfix/api-performance-issue    # API性能問題
```

## 🔄 標準工作流程

### 1. 功能開發流程

#### 創建功能分支
```bash
# 從develop分支創建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/user-auth-login

# 推送到遠程
git push -u origin feature/user-auth-login
```

#### SDD規格驅動開發
```bash
# 1. 規格創建階段
git add .kiro/specs/user-auth/spec.json
git commit -m "spec: 初始化用戶登錄功能規格

- 創建功能規格文件
- 設置初始狀態為requirements階段
- 準備BDD測試目錄結構"

# 2. 需求分析階段  
git add .kiro/specs/user-auth/requirements.md
git commit -m "requirements(user-auth): 完成BDD需求分析

- 定義用戶登錄業務流程
- 創建Gherkin測試場景
- 識別安全性和性能要求
- business-analyst: 需求分析完成"

# 3. 技術設計階段
git add .kiro/specs/user-auth/design.md
git commit -m "design(user-auth): 完成DDD技術設計

- 設計用戶認證領域模型
- 定義API接口規範
- 選擇JWT認證方案
- architect: 設計文檔已審核"

# 4. 任務分解階段
git add .kiro/specs/user-auth/tasks.md
git commit -m "tasks(user-auth): 完成任務分解

- 將設計分解為12個具體任務
- 分配給相應的Sub Agents
- 設置TDD實施順序
- 預估開發時間3天"
```

#### 實施開發
```bash
# TDD開發循環
git add tests/unit/test_user_auth.py
git commit -m "test(user-auth): 添加用戶登錄單元測試

- 測試用戶密碼驗證邏輯
- 測試JWT token生成
- 測試登錄失敗場景
- test-engineer: 測試覆蓋率85%"

git add src/domain/user.py
git commit -m "feat(user-auth): 實現用戶實體和認證邏輯

- 實現User實體類
- 添加密碼加密和驗證
- 實現JWT token生成邏輯
- 通過所有單元測試"

git add src/infrastructure/user_repository.py  
git commit -m "feat(user-auth): 實現用戶倉儲層

- 實現PostgreSQL用戶數據存取
- 添加數據庫連接池
- 實現用戶查詢和創建操作
- data-specialist: 查詢性能優化完成"
```

### 2. 多實例協作流程

#### 角色分支同步
```bash
# 每日同步會議前
git checkout role/business-analyst-$(date +%Y%m%d)
git merge feature/user-auth-login
git push origin role/business-analyst-$(date +%Y%m%d)

# 角色專用提交
git commit -m "analysis: 更新用戶需求分析文檔

- 添加第三方登錄需求
- 更新安全性要求
- 補充邊界條件測試場景
- business-analyst: 需求變更已確認"
```

#### 進度同步機制
```bash
# 創建進度同步標籤
git tag -a "sync-$(date +%Y%m%d)" -m "每日進度同步點

功能進度：
- user-auth: 設計階段完成，開始實施
- api-endpoints: 需求分析進行中
- dashboard-ui: 等待設計審核

角色狀態：
- business-analyst: 2個功能需求完成
- architect: 1個設計文檔待審核
- test-engineer: 測試框架建立完成"

git push origin --tags
```

### 3. 代碼審查流程

#### Pull Request 模板
```markdown
## 功能概述
- **功能名稱**: user-auth-login
- **SDD階段**: implementation
- **負責Agent**: integration-specialist
- **關聯規格**: .kiro/specs/user-auth/

## 變更摘要
- [ ] 實現JWT認證中間件
- [ ] 添加登錄API端點
- [ ] 完成密碼加密邏輯
- [ ] 添加相應單元測試

## 測試狀態
- [ ] 單元測試通過 (15/15)
- [ ] 集成測試通過 (8/8)
- [ ] BDD場景測試通過 (5/5)
- [ ] 代碼覆蓋率: 92%

## 安全檢查
- [ ] 密碼加密實施
- [ ] SQL注入防護
- [ ] JWT token安全配置
- [ ] 敏感信息遮蔽

## 文檔更新
- [ ] API文檔已更新
- [ ] 規格文檔已同步
- [ ] README使用說明已更新

## Agent審核
- [ ] architect: 架構設計符合規範
- [ ] test-engineer: 測試覆蓋充分  
- [ ] business-analyst: 需求實現完整
```

### 4. 發布流程

#### 準備發布分支
```bash
# 創建發布分支
git checkout develop
git checkout -b release/v1.0.0

# 更新版本信息
echo "v1.0.0" > VERSION
git add VERSION
git commit -m "release: 準備v1.0.0發布

功能包含：
- 用戶認證系統
- REST API框架  
- 基礎儀表板
- 完整測試套件

測試狀態：
- 所有BDD場景通過
- 代碼覆蓋率 89%
- 性能測試通過
- 安全審計完成"
```

#### 合併到主分支
```bash
# 合併到main
git checkout main
git merge --no-ff release/v1.0.0
git tag -a "v1.0.0" -m "Release version 1.0.0

包含功能：
- 用戶認證和授權系統
- RESTful API框架
- 響應式用戶界面
- 自動化測試和CI/CD

技術亮點：
- 基於DDD的清晰架構
- 90%以上的測試覆蓋率
- 完整的API文檔
- AI協作開發流程"

git push origin main
git push origin --tags

# 回合併到develop
git checkout develop  
git merge main
git push origin develop
```

## 📝 提交信息規範

### 提交類型 (Type)
```
feat:     新功能
fix:      錯誤修復
docs:     文檔更新
style:    代碼格式化
refactor: 代碼重構
test:     測試相關
chore:    構建和工具相關
spec:     規格文檔相關
analysis: 需求分析相關
design:   技術設計相關
tasks:    任務分解相關
```

### 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 提交信息示例
```bash
# 功能實現
git commit -m "feat(auth): 實現JWT認證中間件

- 添加token生成和驗證邏輯
- 實現認證裝飾器
- 添加權限檢查機制
- 集成Redis token緩存

Closes: #123
Reviewed-by: architect"

# 錯誤修復
git commit -m "fix(api): 修復用戶查詢性能問題

- 優化數據庫查詢索引
- 添加查詢結果緩存
- 修復N+1查詢問題
- 響應時間從500ms降至50ms

Performance: 10x improvement
Tested-by: test-engineer"

# 文檔更新
git commit -m "docs(api): 更新REST API文檔

- 添加認證端點說明
- 更新錯誤碼列表
- 添加請求響應示例
- 修復文檔格式問題

Updated-by: integration-specialist"
```

## 🔄 自動化工作流

### Git Hooks 集成

#### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "🔍 運行pre-commit檢查..."

# 代碼格式檢查
if ! python .claude/scheduler/quality_check.py; then
    echo "❌ 代碼品質檢查失敗"
    exit 1
fi

# 測試運行
if [ -f "pytest" ]; then
    if ! python -m pytest tests/ -x; then
        echo "❌ 測試失敗"
        exit 1
    fi
fi

echo "✅ Pre-commit檢查通過"
```

#### Commit-msg Hook
```bash
#!/bin/bash
# .git/hooks/commit-msg

commit_regex='^(feat|fix|docs|style|refactor|test|chore|spec|analysis|design|tasks)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "❌ 提交信息格式錯誤"
    echo "格式: <type>(<scope>): <subject>"
    echo "例如: feat(auth): 添加用戶登錄功能"
    exit 1
fi

echo "✅ 提交信息格式正確"
```

### 分支保護規則

#### Main分支保護
```yaml
# .github/branch_protection.yml
main:
  protect: true
  required_status_checks:
    strict: true
    contexts:
      - "continuous-integration"
      - "code-quality-check"
      - "security-scan"
  enforce_admins: true
  required_pull_request_reviews:
    required_approving_review_count: 2
    dismiss_stale_reviews: true
  restrictions: null
```

## 📊 Git工作流監控

### 分支狀態檢查
```bash
# 檢查分支狀態腳本
#!/bin/bash
# scripts/git_status_check.sh

echo "📊 Git工作流狀態檢查"
echo "========================"

# 檢查未合併的功能分支
echo "🌿 活躍功能分支:"
git branch -r | grep "feature/" | while read branch; do
    echo "  $branch"
    git log --oneline "$branch" ^develop | head -3 | sed 's/^/    /'
done

# 檢查角色分支
echo "👥 角色專用分支:"
git branch -r | grep "role/" | while read branch; do
    last_commit=$(git log -1 --format="%cd" --date=short "$branch")
    echo "  $branch (最後更新: $last_commit)"
done

# 檢查待發布功能
echo "🚀 待發布功能:"
git log develop ^main --oneline --grep="feat" | head -10
```

### 協作統計
```bash
# Git協作統計腳本
#!/bin/bash
# scripts/collaboration_stats.sh

echo "📈 協作開發統計"
echo "==================="

# Agent提交統計
echo "🤖 Agent提交統計:"
for agent in business-analyst architect data-specialist integration-specialist test-engineer; do
    count=$(git log --all --grep="$agent" --oneline | wc -l)
    echo "  $agent: $count 次提交"
done

# 功能開發進度
echo "📋 功能開發進度:"
for spec in .kiro/specs/*/; do
    if [ -d "$spec" ]; then
        spec_name=$(basename "$spec")
        status=$(grep -o '"status": "[^"]*"' "$spec/spec.json" 2>/dev/null | cut -d'"' -f4)
        echo "  $spec_name: $status"
    fi
done
```

這個Git工作流程確保了：
- 🔄 **清晰的分支管理**
- 👥 **多實例協作同步**  
- 📝 **標準化的提交信息**
- 🔍 **自動化品質檢查**
- 📊 **可追蹤的開發進度**