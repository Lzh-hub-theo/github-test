# CLAUDE.md

该文件为使用 Claude Code (claude.ai/code) 处理此仓库代码提供指导

## 常用命令
- `ls`: 列出仓库文件（重点关注 .git 和 note 目录结构）
- `git status`: 查看工作区状态（在执行破坏性操作前请务必检查）
- `git log --oneline`: 查看提交历史（最新提交为 823bfd3）

## 项目架构
- 简单的笔记系统，在 note/ 目录下使用 markdown/文本文件存储文档
- Git 管理的版本控制系统，包含标准 `.git` 目录结构：
  - 对象存储在 `objects/` 目录下
  - 本地分支引用保存在 `.git/refs/heads/` 目录
  - 提交历史记录保存在 `.git/logs/` 目录