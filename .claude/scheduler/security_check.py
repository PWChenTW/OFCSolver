#!/usr/bin/env python3
"""
安全自動檢查腳本
在Claude Code完成響應後自動檢查安全相關問題
"""

import os
import sys
import re
import glob
from datetime import datetime
import json


class SecurityChecker:
    def __init__(self):
        self.warnings = []
        self.errors = []

    def check_recent_files(self, minutes=10):
        """檢查最近修改的文件"""
        import time

        current_time = time.time()
        cutoff_time = current_time - (minutes * 60)

        # 檢查各類代碼文件
        for pattern in ["**/*.py", "**/*.js", "**/*.ts", "src/**/*", "app/**/*"]:
            for filepath in glob.glob(pattern, recursive=True):
                if os.path.exists(filepath) and os.path.isfile(filepath):
                    if os.path.getmtime(filepath) > cutoff_time:
                        self._check_file_content(filepath)

    def _check_file_content(self, filepath):
        """檢查文件內容的安全問題"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # 檢查是否有硬編碼的敏感信息
            self._check_sensitive_data(filepath, content)

            # 檢查認證和授權
            self._check_authentication(filepath, content)

            # 檢查輸入驗證
            self._check_input_validation(filepath, content)

            # 檢查是否有適當的錯誤處理
            self._check_error_handling(filepath, content)

            # 檢查加密相關
            self._check_encryption(filepath, content)

        except Exception as e:
            self.warnings.append(f"無法檢查文件 {filepath}: {e}")

    def _check_sensitive_data(self, filepath, content):
        """檢查敏感數據"""
        sensitive_patterns = [
            (r'api[_-]?key\s*[:=]\s*["\'](?!.*\{)[^"\']{10,}', "API密鑰可能被硬編碼"),
            (r'password\s*[:=]\s*["\'][^"\']{3,}', "密碼可能被硬編碼"),
            (r'secret\s*[:=]\s*["\'][^"\']{10,}', "秘密可能被硬編碼"),
            (r'token\s*[:=]\s*["\'][^"\']{10,}', "Token可能被硬編碼"),
            (r'private[_-]?key\s*[:=]\s*["\'][^"\']+', "私鑰可能被硬編碼"),
            (
                r'connection[_-]?string\s*[:=]\s*["\'][^"\']+',
                "數據庫連接字符串可能被硬編碼",
            ),
        ]

        for pattern, description in sensitive_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.errors.append(f"🔒 安全警告: {filepath} {description}")

    def _check_authentication(self, filepath, content):
        """檢查認證機制"""
        # 查找認證相關函數
        auth_patterns = [
            r"def\s+.*(?:login|auth|authenticate|signin)",
            r"class\s+.*(?:Auth|Authentication|Login)",
            r"function\s+.*(?:login|auth|authenticate)",
        ]

        has_auth_logic = any(
            re.search(pattern, content, re.IGNORECASE) for pattern in auth_patterns
        )

        if has_auth_logic:
            # 檢查是否有適當的安全措施
            security_patterns = [
                r"bcrypt|argon2|pbkdf2|scrypt",  # 密碼哈希
                r"jwt|token|session",  # 會話管理
                r"csrf|xsrf",  # CSRF保護
                r"rate[_-]?limit",  # 速率限制
                r"captcha|recaptcha",  # 驗證碼
            ]

            has_security = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in security_patterns
            )

            if not has_security:
                self.warnings.append(f"⚠️ 安全提醒: {filepath} 包含認證邏輯但可能缺少安全措施")

    def _check_input_validation(self, filepath, content):
        """檢查輸入驗證"""
        # 查找用戶輸入處理
        input_patterns = [
            r"request\.",
            r"req\.",
            r"input\s*\(",
            r"form\.",
            r"query\s*\[",
            r"params\s*\[",
            r"body\s*\.",
        ]

        has_input_handling = any(
            re.search(pattern, content, re.IGNORECASE) for pattern in input_patterns
        )

        if has_input_handling:
            # 檢查是否有驗證
            validation_patterns = [
                r"validate|validation|validator",
                r"sanitize|escape",
                r"schema\.",
                r"is[A-Z]\w+\(",  # isEmail, isNumber等
                r"test\s*\(",  # 正則測試
                r"match\s*\(",
            ]

            has_validation = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in validation_patterns
            )

            if not has_validation:
                self.warnings.append(f"🛡️ 安全提醒: {filepath} 處理用戶輸入但可能缺少驗證")

    def _check_error_handling(self, filepath, content):
        """檢查錯誤處理"""
        # 查找API調用或外部依賴
        external_call_patterns = [
            r"fetch\s*\(",
            r"axios\.",
            r"http\.",
            r"requests\.",
            r"api\.",
            r"client\.",
            r"\.get\s*\(",
            r"\.post\s*\(",
            r"connect\s*\(",
        ]

        has_external_calls = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in external_call_patterns
        )

        if has_external_calls:
            # 檢查是否有錯誤處理
            error_handling_patterns = [
                r"try[\s:{\(]",
                r"catch[\s\(]",
                r"except[\s:]",
                r"\.catch\s*\(",
                r"error\s*=>",
                r'on\s*\(\s*[\'"]error',
            ]

            has_error_handling = any(
                re.search(pattern, content) for pattern in error_handling_patterns
            )

            if not has_error_handling:
                self.warnings.append(f"🔧 品質提醒: {filepath} 有外部調用但可能缺少錯誤處理")

    def _check_encryption(self, filepath, content):
        """檢查加密相關"""
        # 查找敏感數據處理
        sensitive_data_patterns = [
            r"password|passwd",
            r"credit[_-]?card",
            r"ssn|social[_-]?security",
            r"bank[_-]?account",
            r"private[_-]?key",
        ]

        has_sensitive_data = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in sensitive_data_patterns
        )

        if has_sensitive_data:
            # 檢查是否有加密
            encryption_patterns = [
                r"encrypt|decrypt",
                r"crypto|cipher",
                r"hash\s*\(",
                r"bcrypt|argon2",
                r"aes|rsa",
                r"ssl|tls|https",
            ]

            has_encryption = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in encryption_patterns
            )

            if not has_encryption:
                self.warnings.append(f"🔐 安全提醒: {filepath} 處理敏感數據但可能缺少加密保護")

    def check_git_changes(self):
        """檢查Git變更中的安全問題"""
        try:
            import subprocess

            # 獲取最近的變更
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            if result.returncode == 0:
                changed_files = result.stdout.strip().split("\n")
                for filepath in changed_files:
                    if (
                        filepath
                        and os.path.exists(filepath)
                        and os.path.isfile(filepath)
                    ):
                        self._check_file_content(filepath)
        except Exception:
            # Git檢查失敗不影響主要功能
            pass

    def generate_report(self):
        """生成安全檢查報告"""
        if not self.warnings and not self.errors:
            return None

        report = {
            "timestamp": datetime.now().isoformat(),
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": {
                "total_errors": len(self.errors),
                "total_warnings": len(self.warnings),
                "security_level": (
                    "HIGH" if self.errors else "MEDIUM" if self.warnings else "LOW"
                ),
            },
        }

        return report

    def save_report(self, report, filename=".security_check_report.json"):
        """保存安全報告"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # 靜默失敗，不影響主流程


def main():
    """主函數"""
    checker = SecurityChecker()

    # 檢查最近修改的文件
    checker.check_recent_files(minutes=10)

    # 檢查Git變更
    checker.check_git_changes()

    # 生成報告
    report = checker.generate_report()

    if report:
        # 保存報告
        checker.save_report(report)

        # 輸出關鍵警告
        if checker.errors:
            print("🚨 發現安全問題:")
            for error in checker.errors:
                print(f"  {error}")

        if checker.warnings and len(checker.warnings) <= 3:
            print("⚠️ 安全提醒:")
            for warning in checker.warnings:
                print(f"  {warning}")
        elif checker.warnings:
            print(f"⚠️ 發現 {len(checker.warnings)} 個安全提醒，詳情請查看報告")

    # 返回0表示成功（即使有警告）
    return 0


if __name__ == "__main__":
    sys.exit(main())
