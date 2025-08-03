# Claude Code Agents 協作快速參考指南

## 🚨 任務開始前 - 強制檢查清單

### ⚡ 60秒快速評估
```
□ 新檔案超過 50 行？
□ 超過 3 個類別/函數？
□ 涉及多模組協調？
□ 包含演算法/錯誤處理？
□ 需要理解用戶需求？
□ 涉及並發/異步處理？

如果任何一項為「是」→ 立即委派！
```

## 🎯 委派決策矩陣

| 任務特徵 | 必須委派 | 原因 |
|---------|---------|------|
| 新功能開發 | business-analyst → architect | 需求+架構 |
| API 設計 | business-analyst → integration-specialist | 介面+用戶需求 |
| 演算法實作 | data-specialist → test-engineer | 邏輯+驗證 |
| 錯誤處理 | data-specialist → test-engineer | 策略+場景 |
| 監控儀表板 | business-analyst → data-specialist | 需求+指標 |
| 資料庫設計 | architect → data-specialist | 結構+優化 |
| 安全認證 | architect → integration-specialist → test-engineer | 架構+整合+測試 |

## 🔄 標準委派流程

### 階段 1：需求與設計（並行）
```
business-analyst（需求分析）
architect（架構設計）
data-specialist（演算法設計）
```

### 階段 2：技術與品質（序列）
```
tech-lead（技術審查）→ test-engineer（測試策略）
```

### 階段 3：整合與文檔（並行）
```
integration-specialist（系統整合）
context-manager（文檔更新）
```

## ⚠️ 常見錯誤 vs 正確做法

| ❌ 錯誤做法 | ✅ 正確做法 |
|-----------|-----------|
| 「這很簡單，直接做」 | 執行複雜度評估檢查清單 |
| 只委派一個 agent | 多階段委派流程 |
| 不等回應就實作 | 等待所有必要的專業建議 |
| 忽略 agent 建議 | 整合所有建議到實作計劃 |
| 跳過複雜度評估 | 強制執行評估機制 |

## 🪞 完成後自我反思

### 必答問題
1. 🤔 我是否正確評估了任務複雜度？
2. 🤔 我是否委派了所有應該委派的部分？
3. 🤔 哪些 Sub Agent 應該參與但沒有參與？
4. 🤔 如果重新來過，我會如何改進？

## 📋 委派執行模板

```markdown
## 任務委派執行確認

### 任務：[任務名稱]
- 複雜度：簡單/中等/複雜
- 預估行數：_____

### 委派記錄
- [ ] business-analyst：是/否/不需要
- [ ] architect：是/否/不需要  
- [ ] data-specialist：是/否/不需要
- [ ] integration-specialist：是/否/不需要
- [ ] test-engineer：是/否/不需要
- [ ] tech-lead：是/否/不需要
- [ ] context-manager：是/否/不需要

### 確認聲明
- [ ] 已收到所有必要的專業建議
- [ ] 所有建議已整合到實作計劃中
- [ ] 準備開始實作
```

## 🎉 協作成熟度目標

**當前目標**：從 Level 1（初學者）提升到 Level 2（熟練者）
- ✅ 能夠自動執行複雜度評估
- ✅ 正確委派大部分任務  
- ✅ 開始理解多階段協作

**提升方法**：
1. 嚴格執行檢查清單
2. 學習案例分析  
3. 培養複雜度直覺

---

💡 **記住**：好的協作不是為了完美，而是為了避免重大錯誤和提升品質！