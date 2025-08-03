#!/usr/bin/env python3
"""
任務日誌更新腳本
用於在每次完成任務後自動更新任務日誌
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
import shutil
from typing import List, Dict, Optional


class TaskLogger:
    """管理任務日誌的記錄和歸檔"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.log_dir = self.project_root / ".kiro" / "logs"
        self.log_file = self.log_dir / "task_log.md"
        self.archive_dir = self.log_dir / "archive"
        
        # 確保目錄存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)
    
    def add_task_entry(self, 
                      task_description: str,
                      task_type: str,
                      affected_files: List[str],
                      summary_points: List[str],
                      related_tags: Optional[List[str]] = None) -> None:
        """
        添加新的任務記錄
        
        Args:
            task_description: 任務描述
            task_type: 任務類型 (功能開發/Bug修復/重構/文檔更新/測試/其他)
            affected_files: 影響的檔案列表
            summary_points: 變更摘要點
            related_tags: 相關標籤
        """
        # 讀取現有內容
        if self.log_file.exists():
            content = self.log_file.read_text(encoding='utf-8')
        else:
            content = self._create_initial_log()
        
        # 生成新記錄
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n### {timestamp}\n"
        entry += f"**任務**: {task_description}\n"
        entry += f"**類型**: {task_type}\n"
        entry += "**影響檔案**: \n"
        for file in affected_files:
            entry += f"- `{file}`\n"
        entry += "**變更摘要**: \n"
        for point in summary_points:
            entry += f"- {point}\n"
        if related_tags:
            entry += f"**相關議題**: {' '.join(related_tags)}\n"
        entry += "\n---\n"
        
        # 將新記錄添加到檔案末尾
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        print(f"✅ 任務記錄已添加到 {self.log_file}")
    
    def _create_initial_log(self) -> str:
        """創建初始日誌檔案內容"""
        return """# 任務執行日誌

> 本文檔記錄所有重要的開發任務和變更。每週日自動歸檔到 archive/ 目錄。

## 記錄格式說明

每個任務記錄應包含：
- **時間戳記**：YYYY-MM-DD HH:MM
- **任務描述**：簡短說明做了什麼
- **任務類型**：功能開發/Bug修復/重構/文檔更新/測試/其他
- **影響檔案**：列出修改或新增的主要檔案
- **變更摘要**：簡述主要變更內容（3-5點）
- **相關議題**：如有相關的 issue 或 feature 標籤

---

## 任務記錄
"""
    
    def archive_if_needed(self) -> None:
        """如果是週日，將當前日誌歸檔"""
        today = datetime.now()
        
        # 檢查是否是週日 (weekday() == 6)
        if today.weekday() == 6:
            self._archive_current_log()
    
    def _archive_current_log(self) -> None:
        """歸檔當前日誌"""
        if not self.log_file.exists():
            return
        
        # 生成歸檔檔名 (使用週的開始日期)
        today = datetime.now()
        week_start = today - datetime.timedelta(days=6)
        archive_name = f"task_log_{week_start.strftime('%Y%m%d')}_{today.strftime('%Y%m%d')}.md"
        archive_path = self.archive_dir / archive_name
        
        # 複製檔案到歸檔目錄
        shutil.copy2(self.log_file, archive_path)
        
        # 創建新的空日誌檔案
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(self._create_initial_log())
        
        print(f"📦 日誌已歸檔到 {archive_path}")
    
    def get_recent_tasks(self, days: int = 7) -> List[Dict[str, str]]:
        """獲取最近幾天的任務記錄"""
        # 實作省略，可根據需要添加
        pass


def main():
    """主函數 - 交互式添加任務記錄"""
    logger = TaskLogger()
    
    # 檢查是否需要歸檔
    logger.archive_if_needed()
    
    print("📝 任務記錄工具")
    print("=" * 50)
    
    # 收集任務信息
    task_description = input("任務描述: ").strip()
    if not task_description:
        print("❌ 任務描述不能為空")
        return
    
    print("\n任務類型選項：")
    print("1. 功能開發")
    print("2. Bug修復")
    print("3. 重構")
    print("4. 文檔更新")
    print("5. 測試")
    print("6. 其他")
    
    type_choice = input("選擇任務類型 (1-6): ").strip()
    task_types = {
        "1": "功能開發",
        "2": "Bug修復",
        "3": "重構",
        "4": "文檔更新",
        "5": "測試",
        "6": "其他"
    }
    task_type = task_types.get(type_choice, "其他")
    
    # 收集影響檔案
    print("\n輸入影響的檔案 (每行一個，輸入空行結束):")
    affected_files = []
    while True:
        file = input().strip()
        if not file:
            break
        affected_files.append(file)
    
    if not affected_files:
        print("⚠️  警告：沒有記錄影響的檔案")
    
    # 收集變更摘要
    print("\n輸入變更摘要點 (每行一個，輸入空行結束):")
    summary_points = []
    while True:
        point = input().strip()
        if not point:
            break
        summary_points.append(point)
    
    if not summary_points:
        print("❌ 至少需要一個變更摘要點")
        return
    
    # 相關標籤
    tags_input = input("\n相關標籤 (用空格分隔，可選): ").strip()
    related_tags = [f"#{tag}" for tag in tags_input.split()] if tags_input else None
    
    # 添加記錄
    logger.add_task_entry(
        task_description=task_description,
        task_type=task_type,
        affected_files=affected_files,
        summary_points=summary_points,
        related_tags=related_tags
    )
    
    print("\n✅ 任務記錄完成！")


def quick_log(task_desc: str, files: List[str], summary: List[str], task_type: str = "其他"):
    """快速記錄函數，供程式調用"""
    logger = TaskLogger()
    logger.archive_if_needed()
    logger.add_task_entry(
        task_description=task_desc,
        task_type=task_type,
        affected_files=files,
        summary_points=summary,
        related_tags=None
    )


if __name__ == "__main__":
    # 支援命令行參數快速記錄
    if len(sys.argv) > 1:
        # 格式: python update_task_log.py "任務描述" "file1,file2" "摘要1;摘要2"
        if len(sys.argv) >= 4:
            task_desc = sys.argv[1]
            files = sys.argv[2].split(',')
            summary = sys.argv[3].split(';')
            task_type = sys.argv[4] if len(sys.argv) > 4 else "其他"
            quick_log(task_desc, files, summary, task_type)
        else:
            print("用法: python update_task_log.py \"任務描述\" \"file1,file2\" \"摘要1;摘要2\" [任務類型]")
    else:
        main()