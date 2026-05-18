# CLAUDE.md

该文件为使用 Claude Code (claude.ai/code) 处理此仓库代码提供指导

## 常用命令
 – `ls`: 列出仓库文件（重点关注 .git 和 note 目录结构）
- `git status`: 查看工作区状态（在执行破坏性操作前请务必检查）
- `git log --oneline`: 查看提交历史（最新提交为 87d226a）
- `git log --oneline -5`: 查看最近5条提交历史
- `ls -la note/`: 列出笔记目录的详细内容

## 项目架构
- Git 学习与练习仓库，用于练习 git 基本使用
- 在 note/ 目录下存放学习笔记，包括 markdown 和文本格式文件
- 笔记内容包括：
  - Git 基础命令学习笔记
  - Linux 系统学习笔记
  - Markdown 语法学习笔记
  - Claude Code 使用笔记
- Git 管理的版本控制系统，包含标准 `.git` 目录结构：
  - 对象存储在 `objects/` 目录下
  - 本地分支引用保存在 `.git/refs/heads/` 目录
  - 提交历史记录保存在 `.git/logs/` 目录

## 更新信息
- 2026-04-01: 更新了最新提交信息并添加了更多常用命令描述
- 添加了项目架构的详细描述，说明这是一个 Git 学习练习仓库
- 新增了笔记内容的详细分类说明