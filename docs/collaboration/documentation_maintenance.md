# 文檔維護指南

## 📋 概述

本指南定義了AI協作開發項目的文檔維護策略，確保文檔與代碼保持同步，並為團隊提供準確、實用的信息。

## 📚 文檔體系結構

### 1. 核心配置文檔
```
├── README.md                    # 項目概述和快速開始
├── CLAUDE.md                    # Claude Code 主配置
├── AI_COLLABORATION_TEMPLATE.md # 完整模板說明
└── USAGE_GUIDE.md              # 詳細使用指南
```

**維護責任**: 項目維護者
**更新頻率**: 重大變更時
**觸發條件**: 項目結構變化、新功能發布

### 2. 項目知識庫 (.kiro/steering/)
```
├── product.md          # 產品概述和目標
├── tech.md            # 技術架構決策
├── methodology.md     # 開發方法論
├── business_rules.md  # 業務規則和約束
└── collaboration.md   # 協作規範
```

**維護責任**: business-analyst + architect
**更新頻率**: 每週檢查
**觸發條件**: 需求變更、技術決策變更

### 3. 功能規格文檔 (.kiro/specs/)
```
[feature-name]/
├── spec.json          # 規格狀態追蹤
├── requirements.md    # BDD需求文檔
├── design.md         # DDD設計文檔
└── tasks.md          # 具體任務清單
```

**維護責任**: 對應的Sub Agents
**更新頻率**: 實時更新
**觸發條件**: SDD流程推進、需求變更

### 4. 技術文檔 (docs/)
```
├── quick_reference/   # 快速參考指南
├── collaboration/     # 協作流程文檔
├── checklists/       # 檢查清單
└── examples/         # 使用範例
```

**維護責任**: 相關專業Sub Agents
**更新頻率**: 根據使用反饋
**觸發條件**: API變更、流程優化

## 🔄 文檔生命週期管理

### 1. 創建階段

#### 自動生成機制
```bash
# SDD規格文檔自動創建
> /spec-init "user-management" "用戶管理系統"
# 自動創建：
# - .kiro/specs/user-management/spec.json
# - .kiro/specs/user-management/requirements.md (模板)
# - .kiro/specs/user-management/design.md (模板)
# - .kiro/specs/user-management/tasks.md (模板)
```

#### 文檔模板
```markdown
# [功能名稱] 需求分析

## 文檔信息
- **創建時間**: {timestamp}
- **負責Agent**: business-analyst
- **當前狀態**: requirements
- **最後更新**: {timestamp}

## 業務目標
[待business-analyst填寫]

## 主要場景
[BDD場景待生成]

## 驗收標準
[待定義]

---
📝 本文檔由AI協作開發模板自動生成
🔄 請保持與實際需求同步
```

### 2. 維護階段

#### 自動同步觸發
```yaml
# .claude/settings.json 中的文檔同步Hook
"PostToolUse": [
  {
    "matcher": {
      "tools": ["EditTool", "WriteTool"]
    },
    "hooks": [
      {
        "type": "conditional",
        "condition": "file_path.startswith('src/')",
        "action": "command",
        "command": "python .claude/scheduler/doc_sync_check.py \"$file_path\""
      }
    ]
  }
]
```

#### 文檔同步檢查腳本
```python
#!/usr/bin/env python3
# .claude/scheduler/doc_sync_check.py

import sys
import os
import json
from datetime import datetime

def check_doc_sync(modified_file):
    """檢查修改的代碼文件是否需要更新文檔"""
    
    # 檢查是否是核心文件
    if any(modified_file.startswith(path) for path in ['src/domain/', 'src/application/']):
        print(f"🔄 代碼文件 {modified_file} 已修改，請檢查相關文檔是否需要更新：")
        
        # 查找相關規格文檔
        for spec_dir in os.listdir('.kiro/specs/'):
            spec_path = f'.kiro/specs/{spec_dir}'
            if os.path.isdir(spec_path):
                print(f"  - {spec_path}/design.md")
                print(f"  - {spec_path}/requirements.md")
        
        # 檢查API文檔
        if 'api' in modified_file.lower():
            print("  - docs/quick_reference/api_design.md")
            print("  - README.md (如果有API變更)")
        
        print("💡 建議使用: > 請檢查並更新相關文檔")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_doc_sync(sys.argv[1])
```

### 3. 版本控制

#### 文檔版本標記
```markdown
# 用戶管理系統 - 需求分析

**文檔版本**: v1.2.0
**最後更新**: 2024-01-27 15:30
**更新者**: business-analyst
**變更摘要**: 添加第三方登錄需求

## 版本歷史
- v1.2.0 (2024-01-27): 添加第三方登錄需求
- v1.1.0 (2024-01-25): 更新安全性要求
- v1.0.0 (2024-01-20): 初始版本
```

#### Git提交關聯
```bash
# 文檔更新提交
git commit -m "docs(user-mgmt): 更新用戶管理需求文檔 v1.2.0

- 添加Google/Facebook第三方登錄需求
- 更新安全性要求章節
- 補充邊界條件測試場景
- 關聯功能: src/auth/oauth.py

business-analyst: 需求變更已確認
architect: 設計影響評估待進行"

# 代碼和文檔同步提交
git commit -m "feat(auth): 實現OAuth第三方登錄

代碼變更:
- 添加OAuth認證服務
- 實現Google/Facebook登錄
- 更新用戶模型

文檔同步:
- 更新API文檔
- 同步需求規格
- 更新使用指南

Closes: #456
Docs-updated: user-mgmt/requirements.md v1.2.0"
```

## 📊 文檔質量保證

### 1. 自動化檢查

#### 文檔一致性檢查
```python
#!/usr/bin/env python3
# scripts/doc_quality_check.py

import os
import re
import json
from datetime import datetime, timedelta

class DocumentationChecker:
    def __init__(self):
        self.issues = []
        
    def check_spec_consistency(self):
        """檢查規格文檔一致性"""
        for spec_dir in os.listdir('.kiro/specs/'):
            spec_path = f'.kiro/specs/{spec_dir}'
            if not os.path.isdir(spec_path):
                continue
                
            # 檢查必需文件
            required_files = ['spec.json', 'requirements.md', 'design.md', 'tasks.md']
            for file in required_files:
                if not os.path.exists(f'{spec_path}/{file}'):
                    self.issues.append(f"❌ 缺少文件: {spec_path}/{file}")
            
            # 檢查狀態一致性
            try:
                with open(f'{spec_path}/spec.json', 'r') as f:
                    spec_data = json.load(f)
                    status = spec_data.get('status', 'unknown')
                    
                # 檢查文檔內容與狀態的一致性
                self._check_status_consistency(spec_path, status)
                
            except Exception as e:
                self.issues.append(f"❌ 無法讀取規格文件: {spec_path}/spec.json - {e}")
    
    def check_documentation_freshness(self):
        """檢查文檔新鮮度"""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for root, dirs, files in os.walk('docs/'):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if mtime < cutoff_date:
                        self.issues.append(f"⚠️ 文檔可能過期: {file_path} (最後更新: {mtime.strftime('%Y-%m-%d')})")
    
    def check_broken_links(self):
        """檢查文檔中的內部鏈接"""
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 檢查相對路徑鏈接
                    links = re.findall(r'\[.*?\]\(([^)]+)\)', content)
                    for link in links:
                        if not link.startswith('http') and not link.startswith('#'):
                            link_path = os.path.join(os.path.dirname(file_path), link)
                            if not os.path.exists(link_path):
                                self.issues.append(f"🔗 斷開的鏈接: {file_path} -> {link}")
    
    def generate_report(self):
        """生成文檔質量報告"""
        if not self.issues:
            return "✅ 文檔質量檢查通過"
        
        report = "📋 文檔質量檢查報告\n"
        report += "=" * 30 + "\n"
        report += f"發現 {len(self.issues)} 個問題:\n\n"
        
        for issue in self.issues:
            report += f"{issue}\n"
        
        return report

if __name__ == "__main__":
    checker = DocumentationChecker()
    checker.check_spec_consistency()
    checker.check_documentation_freshness()
    checker.check_broken_links()
    
    print(checker.generate_report())
```

### 2. 定期審查

#### 文檔審查檢查清單
```markdown
# 文檔審查檢查清單

## 每週檢查 (每週一)
- [ ] 檢查所有active規格文檔是否與代碼同步
- [ ] 審查.kiro/steering/內容是否需要更新
- [ ] 檢查README.md是否反映最新項目狀態
- [ ] 驗證快速參考文檔的準確性

## 每月檢查 (月初)
- [ ] 運行文檔質量檢查腳本
- [ ] 審查並清理過期的規格文檔
- [ ] 更新使用指南和最佳實踐
- [ ] 收集用戶反饋並改進文檔

## 發布前檢查
- [ ] 確保所有API變更已記錄
- [ ] 更新CHANGELOG和版本信息
- [ ] 檢查示例代碼是否仍然有效
- [ ] 驗證安裝和設置說明
```

### 3. 用戶反饋機制

#### 文檔改進追蹤
```markdown
# 文檔改進追蹤

## 用戶反饋收集
- GitHub Issues標記為 `documentation`
- 在文檔底部添加反饋鏈接
- 定期調查文檔使用體驗

## 改進優先級
1. **高優先級**: 錯誤信息、缺失的關鍵步驟
2. **中優先級**: 改進清晰度、添加示例
3. **低優先級**: 格式優化、補充細節

## 改進流程
1. 收集反饋 → 2. 評估影響 → 3. 分配責任 → 4. 實施改進 → 5. 驗證效果
```

## 🤖 Sub Agent文檔責任

### business-analyst
**負責文檔**:
- `.kiro/specs/*/requirements.md`
- `docs/examples/bdd_scenarios.md`
- 用戶故事和業務流程文檔

**維護任務**:
- 確保BDD場景準確反映業務需求
- 更新業務規則變更
- 維護用戶故事的可追溯性

### architect  
**負責文檔**:
- `.kiro/specs/*/design.md`
- `.kiro/steering/tech.md`
- `docs/quick_reference/design_patterns.md`

**維護任務**:
- 同步架構決策記錄(ADR)
- 更新技術選型理由
- 維護系統架構圖

### data-specialist
**負責文檔**:
- 算法實現文檔
- 性能優化記錄
- `docs/quick_reference/data_structures.md`

**維護任務**:
- 文檔化算法選擇理由
- 更新性能基準測試結果
- 維護數據結構設計說明

### integration-specialist
**負責文檔**:
- API文檔
- 集成指南  
- `docs/quick_reference/api_design.md`

**維護任務**:
- 保持API文檔與實現同步
- 更新集成示例代碼
- 維護錯誤碼和響應格式文檔

### test-engineer
**負責文檔**:
- 測試策略文檔
- 測試用例文檔
- `docs/checklists/`相關內容

**維護任務**:
- 更新測試覆蓋率報告
- 維護測試環境設置文檔
- 記錄測試最佳實踐

## 📈 文檔指標追蹤

### 關鍵指標
```python
# 文檔指標腳本
#!/usr/bin/env python3
# scripts/doc_metrics.py

def calculate_doc_metrics():
    """計算文檔相關指標"""
    
    metrics = {
        'total_docs': 0,
        'outdated_docs': 0,
        'spec_completion_rate': 0,
        'broken_links': 0,
        'doc_code_sync_rate': 0
    }
    
    # 統計文檔總數
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.md'):
                metrics['total_docs'] += 1
    
    # 計算規格完成率
    spec_dirs = [d for d in os.listdir('.kiro/specs/') if os.path.isdir(f'.kiro/specs/{d}')]
    completed_specs = 0
    
    for spec_dir in spec_dirs:
        spec_path = f'.kiro/specs/{spec_dir}/spec.json'
        if os.path.exists(spec_path):
            with open(spec_path, 'r') as f:
                spec_data = json.load(f)
                if spec_data.get('status') == 'completed':
                    completed_specs += 1
    
    if spec_dirs:
        metrics['spec_completion_rate'] = (completed_specs / len(spec_dirs)) * 100
    
    return metrics

if __name__ == "__main__":
    metrics = calculate_doc_metrics()
    print("📊 文檔指標報告")
    print("=" * 20)
    for key, value in metrics.items():
        print(f"{key}: {value}")
```

### 改進目標
- 文檔完整性: > 95%
- 文檔時效性: < 30天未更新的文檔 < 10%
- 斷鏈率: < 1%
- 用戶滿意度: > 4.0/5.0

這個文檔維護體系確保了：
- 📚 **完整的文檔結構**
- 🔄 **自動化同步機制**
- 👥 **明確的維護責任**
- 📊 **量化的質量指標**
- 🔍 **持續的改進流程**