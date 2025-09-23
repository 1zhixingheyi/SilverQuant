# CCPM全流程命令详细指南

## 文档说明

**官方信息源**: [CCPM GitHub仓库](https://github.com/automazeio/ccpm)
**验证日期**: 2025-01-19
**基于版本**: Main分支（最新版本）
**验证方法**: 基于官方命令定义文件和官方README.md

**内容来源**:
- 所有命令语法基于 `.claude/commands/pm/` 目录下的官方命令定义文件
- 工作流程基于官方README.md的系统架构和工作流程说明
- 参数和示例基于官方命令文件中的具体实现逻辑

---

## CCPM概述

CCPM是Claude Code项目管理系统，通过GitHub Issues和Git Worktrees实现并行AI代理开发。核心理念是**规范驱动开发**，确保每行代码都能追溯到明确的规范。

### 核心特性
- **5阶段工作流程**: Brainstorm → Document → Plan → Execute → Track
- **并行AI执行**: 多个Claude实例可同时工作在不同任务上
- **GitHub原生集成**: 使用Issues作为数据库，无需额外工具
- **Context保持**: 每个Epic维护独立上下文，避免信息丢失

---

## 完整工作流程概述

```
阶段1: 系统初始化 (/pm:init)
   ↓
阶段2: 创建PRD (/pm:prd-new feature-name)
   ↓
阶段3: PRD转技术方案 (/pm:prd-parse feature-name)
   ↓
阶段4: 分解并同步 (/pm:epic-oneshot feature-name)
   ↓
阶段5: 并行执行 (/pm:epic-start feature-name)
   ↓
阶段6: 状态跟踪 (/pm:status, /pm:epic-show)
```

---

## 第一阶段：系统初始化

### `/pm:init` - 初始化CCPM系统

**官方来源**: `.claude/commands/pm/init.md`

#### 命令语法
```bash
/pm:init
```

#### 功能说明
运行初始化脚本设置CCPM项目管理环境，包括：
- 安装GitHub CLI（如果需要）
- 认证GitHub账户
- 安装gh-sub-issue扩展（用于父子Issue关系）
- 创建必需目录结构
- 更新.gitignore文件

#### 前置条件
- 当前目录是Git仓库
- 有网络连接用于下载依赖
- 有GitHub账户访问权限

#### 执行过程
```bash
# 1. 执行初始化
/pm:init

# 系统会自动执行以下操作：
# - 运行 bash .claude/scripts/pm/init.sh
# - 安装和配置GitHub CLI
# - 设置认证
# - 创建目录结构

# 2. 验证初始化成功
/pm:help
```

#### 预期输出
```
✓ GitHub CLI installed and authenticated
✓ gh-sub-issue extension installed
✓ Project directories created
✓ .gitignore updated
✓ CCPM initialization complete
```

#### 创建的目录结构
```
.claude/
├── prds/              # 产品需求文档存放目录
├── epics/             # Epic和任务文件存放目录
├── context/           # 项目上下文文件
├── commands/pm/       # PM命令定义（已存在）
├── scripts/pm/        # PM脚本文件（已存在）
├── rules/             # 规则驱动机制文件
└── agents/            # 专门代理定义文件
```

#### 规则驱动机制

##### 九大核心规则文件

**官方来源**: `.claude/rules/`目录

1. **agent-coordination.md** - 代理协调规则
2. **time-handling.md** - 时间戳处理规则
3. **git-practices.md** - Git工作流规则
4. **frontmatter-rules.md** - 元数据格式规则
5. **epic-management.md** - Epic管理规则
6. **issue-tracking.md** - Issue跟踪规则
7. **testing-standards.md** - 测试标准规则
8. **documentation.md** - 文档维护规则
9. **security-practices.md** - 安全实践规则

##### 关键规则要点

###### 时间戳规则 (最高优先级)
- 所有时间戳必须使用真实当前时间
- 禁止使用示例或占位符时间
- 时间格式: ISO 8601 (2024-01-19T15:30:00Z)

###### 代理协调规则
- 频繁提交避免冲突
- 明确的提交信息格式
- 进度更新到指定目录
- 文件级别的并行控制

###### Frontmatter规则
- 严格的YAML格式要求
- 必需字段验证
- 时间戳自动更新
- 状态生命周期管理

---

## 第二阶段：创建产品需求文档

### `/pm:prd-new` - 创建新的PRD

**官方来源**: `.claude/commands/pm/prd-new.md`

#### 命令语法
```bash
/pm:prd-new <feature_name>
```

#### 参数说明
- `feature_name`: 功能名称，必须使用kebab-case格式（小写字母、数字、连字符）

#### 功能说明
启动交互式头脑风暴会话，创建全面的产品需求文档。这是整个项目管理流程的起点。

#### 输入验证
```bash
# ✅ 正确的格式
/pm:prd-new user-authentication
/pm:prd-new blog-system
/pm:prd-new api-v2

# ❌ 错误的格式
/pm:prd-new UserAuthentication  # 包含大写字母
/pm:prd-new user_authentication # 包含下划线
/pm:prd-new "user auth"         # 包含空格
```

#### 完整示例：创建博客系统PRD

```bash
# 1. 启动PRD创建
/pm:prd-new blog-system

# 2. 系统会启动交互式会话，引导你完成以下章节：
```

**PRD文件结构**（基于官方模板）:
```yaml
---
name: blog-system
description: "个人博客系统，支持文章发布、评论和用户管理"
status: backlog
created: 2025-01-19T10:30:00Z
---

# Blog System - 产品需求文档

## Executive Summary（执行摘要）
构建一个现代化的个人博客平台，支持文章发布、分类管理、评论系统和基础用户管理功能。

## Problem Statement（问题陈述）
现有博客平台要么功能过于复杂，要么缺乏必要的自定义能力。需要一个简洁但功能完整的博客解决方案。

## User Stories（用户故事）
### 作为博主，我希望能够：
- 创建和发布文章
- 对文章进行分类和标签管理
- 管理评论和读者互动
- 查看访问统计

### 作为读者，我希望能够：
- 浏览和搜索文章
- 对文章进行评论
- 订阅感兴趣的分类

## Requirements（需求）

### 功能性需求
1. **文章管理**
   - 富文本编辑器支持
   - Markdown格式支持
   - 草稿保存功能
   - 文章分类和标签

2. **用户系统**
   - 用户注册和登录
   - 个人资料管理
   - 权限控制（管理员/普通用户）

3. **评论系统**
   - 嵌套评论支持
   - 评论审核机制
   - 反垃圾评论

### 非功能性需求
- 响应时间：页面加载<2秒
- 并发用户：支持1000+同时在线
- 安全性：HTTPS，SQL注入防护
- SEO友好：静态URL，meta标签

## Success Criteria（成功标准）
- [ ] 用户可以在5分钟内完成注册和发布第一篇文章
- [ ] 页面加载时间平均<2秒
- [ ] 评论系统无垃圾评论困扰
- [ ] 移动端用户体验良好

## Constraints & Assumptions（约束和假设）
- 使用现有技术栈（Python + React）
- 预算限制：2周开发时间
- 假设用户熟悉基本的博客概念

## Out of Scope（范围外）
- 多语言支持
- 高级SEO功能
- 社交媒体集成
- 付费订阅功能

## Dependencies（依赖关系）
- 数据库设计完成
- UI设计规范确定
- 域名和托管环境准备
```

#### 输出文件
```
.claude/prds/blog-system.md
```

### 列出PRD - `/pm:prd-list`

**官方来源**: `.claude/commands/pm/prd-list.md`

#### 命令格式与参数
```bash
/pm:prd-list
```

#### 功能说明
调用脚本 `bash .claude/scripts/pm/prd-list.sh`，显示所有PRD文件列表，完整输出不截断。

#### 核心特性
- **完整扫描**: 扫描`.claude/prds/`目录下所有PRD文件
- **状态分析**: 分析每个PRD的frontmatter和关联Epic
- **快速操作**: 为每个PRD提供相应的下一步操作建议
- **智能分类**: 按状态和优先级排序显示

#### 详细使用示例
```bash
# 列出所有PRD及其状态
/pm:prd-list
```

#### 预期输出格式
```
📋 PRD列表 (共4个)
┌─────────────────┬──────────────┬──────────────┬─────────────────┬──────────────┐
│ PRD名称         │ 状态         │ 最后修改     │ 关联Epic        │ 快速操作     │
├─────────────────┼──────────────┼──────────────┼─────────────────┼──────────────┤
│ user-auth       │ ✅ 已实施    │ 2024-01-15   │ epic-user-auth  │ /pm:epic-show│
│ data-storage    │ 🔄 开发中    │ 2024-01-14   │ epic-storage    │ /pm:status   │
│ api-gateway     │ 📋 待解析    │ 2024-01-13   │ -               │ /pm:prd-parse│
│ notification    │ ✏️ 草稿      │ 2024-01-12   │ -               │ /pm:prd-edit │
└─────────────────┴──────────────┴──────────────┴─────────────────┴──────────────┘

🎯 建议下一步:
- 完成 notification PRD 编写: /pm:prd-edit notification
- 解析 api-gateway PRD: /pm:prd-parse api-gateway
- 检查 data-storage 进度: /pm:epic-show data-storage
```

### 编辑PRD - `/pm:prd-edit`

**官方来源**: `.claude/commands/pm/prd-edit.md`

#### 命令格式与参数
```bash
/pm:prd-edit <feature_name>
```

#### 功能说明
编辑现有产品需求文档，支持章节级别的精确修改和版本控制。

#### 核心特性
- **交互式编辑**: 用户选择要编辑的特定章节
- **版本控制**: 保留原始创建日期，更新修改时间
- **Epic关联检查**: 检测PRD关联的Epic并提醒用户审查
- **格式保持**: 严格遵循frontmatter操作规则

#### 可编辑章节
- **Executive Summary** (执行摘要)
- **Problem Statement** (问题陈述)
- **User Stories** (用户故事)
- **Requirements** (功能/非功能需求)
- **Success Criteria** (成功标准)
- **Constraints & Assumptions** (约束和假设)
- **Out of Scope** (超出范围)
- **Dependencies** (依赖关系)

#### 详细使用示例
```bash
# 编辑博客系统PRD
/pm:prd-edit blog-system

# 系统会显示可编辑章节列表
# 用户选择章节进行编辑
# 自动检查关联Epic的影响
```

#### 交互式编辑流程
```
🔧 编辑PRD: blog-system

📋 可编辑章节:
1. Executive Summary (执行摘要)
2. Problem Statement (问题陈述)
3. User Stories (用户故事)
4. Requirements (需求)
5. Success Criteria (成功标准)
6. Constraints & Assumptions (约束假设)
7. Out of Scope (范围外)
8. Dependencies (依赖关系)
9. 全部章节

请选择要编辑的章节 (1-9): 4

⚠️ 注意: 此PRD已关联Epic "epic-blog-system"
修改Requirements可能影响现有任务分解。
编辑完成后建议运行: /pm:epic-sync blog-system

📝 正在编辑 Requirements 章节...
```

#### 预期输出
```
✅ PRD编辑完成: blog-system
📝 修改章节: Requirements
⏰ 更新时间: 2024-01-19 15:30:00
🔗 关联Epic: epic-blog-system (需要同步)

🔄 建议下一步:
/pm:prd-parse blog-system    # 重新生成技术方案
/pm:epic-sync blog-system    # 同步到GitHub
```

### `/pm:prd-status` - 显示PRD实施状态

**官方来源**: `.claude/commands/pm/prd-status.md`

#### 命令语法
```bash
/pm:prd-status <feature_name>
```

#### 功能说明
显示PRD的实施状态，包括关联Epic的进度、任务完成情况和整体实施状态。

#### 使用示例
```bash
# 查看博客系统PRD的实施状态
/pm:prd-status blog-system
```

#### 预期输出格式
```
📋 PRD状态: blog-system

📈 实施进度: 75% 完成
🔗 关联Epic: epic-blog-system (#1230)
📊 任务状态:
  ✅ 已完成: 3个任务
  🔄 进行中: 2个任务
  ⏳ 等待中: 1个任务

🎯 关键里程碑:
  ✅ 数据库设计完成
  🔄 用户认证开发中
  ⏳ 前端界面待开始

💡 建议操作:
  /pm:epic-show blog-system    # 查看详细进度
  /pm:issue-start 1235         # 继续进行中的任务
```

---

## 第三阶段：PRD转技术实现方案

### `/pm:prd-parse` - 转换PRD为技术Epic

**官方来源**: `.claude/commands/pm/prd-parse.md`

#### 命令语法
```bash
/pm:prd-parse <feature_name>
```

#### 前置条件
- PRD文件已存在且格式正确
- PRD的frontmatter包含必需字段

#### 功能说明
将产品需求文档转换为详细的技术实现Epic，包括架构决策、技术方法和任务分解预览。

#### 完整示例：解析博客系统PRD

```bash
# 1. 解析PRD
/pm:prd-parse blog-system

# 2. 系统会分析PRD并创建技术实现方案
```

**Epic文件结构**（基于官方模板）:
```yaml
---
name: blog-system
status: backlog
created: 2025-01-19T11:00:00Z
progress: 0%
prd: .claude/prds/blog-system.md
github: null  # 同步后更新
---

# Blog System - 技术实现Epic

## Overview（概述）
基于Python + React技术栈构建全功能个人博客平台，采用前后端分离架构，确保高性能和良好的用户体验。

## Architecture Decisions（架构决策）

### 后端技术栈
- **Web框架**: FastAPI（异步支持，自动API文档）
- **数据库**: PostgreSQL（关系型数据，支持全文搜索）
- **认证**: JWT + OAuth2（标准化，无状态）
- **缓存**: Redis（会话存储，页面缓存）

### 前端技术栈
- **框架**: React 18（组件化，生态成熟）
- **状态管理**: Zustand（轻量级，易于调试）
- **样式**: Tailwind CSS（快速开发，一致性）
- **富文本**: React-Quill（功能丰富，可扩展）

## Technical Approach（技术方法）

### 数据库设计
- Users (id, username, email, password_hash, role, created_at)
- Posts (id, title, content, slug, status, author_id, created_at, updated_at)
- Categories (id, name, slug, description)
- Tags (id, name, slug)
- Comments (id, post_id, author_id, content, parent_id, created_at)

### API设计
- GET  /api/posts          # 获取文章列表
- POST /api/posts          # 创建文章
- GET  /api/posts/{id}     # 获取单篇文章
- PUT  /api/posts/{id}     # 更新文章
- DELETE /api/posts/{id}   # 删除文章
- POST /api/auth/login     # 用户登录
- POST /api/auth/register  # 用户注册

## Task Breakdown Preview（任务分解预览）
### 数据库相关（2-3个任务）
- 设计数据库schema和迁移脚本
- 实现ORM模型和关系

### 后端API（3-4个任务）
- 用户认证和授权系统
- 文章管理API endpoints
- 评论系统API
- 搜索和过滤功能

### 前端界面（3-4个任务）
- 基础组件库和布局
- 文章展示和编辑界面
- 用户认证界面
- 管理后台界面
```

#### 输出文件
```
.claude/epics/blog-system/epic.md
```

---

## 第四阶段：任务分解和GitHub同步

### `/pm:epic-decompose` - 分解Epic为具体任务

**官方来源**: `.claude/commands/pm/epic-decompose.md`

#### 命令语法
```bash
/pm:epic-decompose <feature_name>
```

#### 功能说明
将Epic分解为具体的、可执行的任务。支持并行创建任务以提高效率。

#### 完整示例：分解博客系统Epic

```bash
# 1. 分解Epic
/pm:epic-decompose blog-system

# 系统会基于Epic内容创建多个任务文件
```

**任务文件示例**（`.claude/epics/blog-system/001.md`）:
```yaml
---
name: "数据库Schema设计和迁移脚本"
status: open
created: 2025-01-19T11:30:00Z
updated: 2025-01-19T11:30:00Z
github: null  # 同步后更新
depends_on: []
parallel: true
conflicts_with: []
---

# 任务001: 数据库Schema设计和迁移脚本

## Description（描述）
设计和实现博客系统的完整数据库schema，包括用户、文章、分类、标签和评论等核心表结构，并创建相应的迁移脚本。

## Acceptance Criteria（验收标准）
- [ ] 完成所有核心表的设计（Users, Posts, Categories, Tags, Comments）
- [ ] 创建Alembic迁移脚本
- [ ] 包含适当的索引和约束
- [ ] 通过数据库设计评审
- [ ] 迁移脚本可以成功执行

## Technical Details（技术细节）
### 表结构设计
- Users表：用户基本信息和认证
- Posts表：文章内容和元数据
- Categories表：文章分类
- Tags表：文章标签
- Comments表：评论系统

### 迁移脚本要求
- 使用Alembic进行版本控制
- 包含回滚脚本
- 添加必要的索引
- 设置外键约束

## Dependencies（依赖关系）
- 无前置依赖，这是基础任务

## Effort Estimate（工作量估计）
- **预估时间**: 4-6小时
- **复杂度**: 中等
- **风险等级**: 低
```

### `/pm:epic-sync` - 同步到GitHub

**官方来源**: `.claude/commands/pm/epic-sync.md`

#### 命令语法
```bash
/pm:epic-sync <feature_name>
```

#### 功能说明
将Epic和所有任务推送到GitHub作为Issues，建立父子关系，并创建工作树用于并行开发。

#### 同步过程详解

1. **创建Epic Issue**
```bash
# 在GitHub创建主Epic Issue
gh issue create --title "Epic: Blog System Implementation" \
  --body-file .claude/epics/blog-system/epic.md \
  --label "epic,epic:blog-system"
```

2. **创建任务Sub-Issues**
```bash
# 为每个任务创建子Issue
gh issue create --title "数据库Schema设计和迁移脚本" \
  --body-file .claude/epics/blog-system/001.md \
  --label "task,epic:blog-system"

# 如果安装了gh-sub-issue扩展，建立父子关系
gh sub-issue create <epic_issue_id> <task_issue_id>
```

3. **文件重命名**
```bash
# 原文件名 -> GitHub Issue ID
001.md -> 1234.md  # 假设Issue ID是1234
002.md -> 1235.md
```

4. **创建工作树**
```bash
# 在项目外创建独立工作目录
git worktree add ../epic-blog-system epic/blog-system
```

#### 输出结果
```
✓ Epic Issue created: #1230
✓ Task Issues created: #1231, #1232, #1233, #1234, #1235
✓ Files renamed to Issue IDs
✓ Worktree created: ../epic-blog-system
✓ Sync complete - ready for parallel development
```

### `/pm:epic-list` - 列出所有Epic

**官方来源**: `.claude/commands/pm/epic-list.md`

#### 命令语法
```bash
/pm:epic-list
```

#### 功能说明
显示所有Epic的列表，包括状态、进度和下一步操作建议。

#### 预期输出
```
📋 Epic列表 (共3个)
┌─────────────────┬──────────────┬──────────────┬─────────────────┬──────────────┐
│ Epic名称        │ 状态         │ 进度         │ GitHub Issue    │ 快速操作     │
├─────────────────┼──────────────┼──────────────┼─────────────────┼──────────────┤
│ user-auth       │ ✅ 已完成    │ 100%         │ #1120           │ /pm:epic-show│
│ blog-system     │ 🔄 进行中    │ 75%          │ #1230           │ /pm:next     │
│ api-gateway     │ 📋 待开始    │ 0%           │ #1340           │ /pm:epic-start│
└─────────────────┴──────────────┴──────────────┴─────────────────┴──────────────┘

🎯 建议下一步:
- 完成 blog-system Epic: /pm:epic-show blog-system
- 开始 api-gateway Epic: /pm:epic-start api-gateway
```

### `/pm:epic-close` - 关闭Epic

**官方来源**: `.claude/commands/pm/epic-close.md`

#### 命令语法
```bash
/pm:epic-close <epic_name>
```

#### 功能说明
标记Epic为完成状态，更新GitHub Issue状态，并可选择性地清理本地文件。

#### 使用示例
```bash
# 关闭博客系统Epic
/pm:epic-close blog-system
```

#### 预期输出
```
✅ Epic关闭: blog-system
📊 最终统计:
  - 总任务数: 5
  - 完成任务: 5
  - 总开发时间: 3天
  - 代码提交: 23次

🔄 GitHub同步:
  ✅ Epic Issue #1230 已关闭
  ✅ 所有子任务已验证完成

🧹 清理选项:
  [Y/N] 删除本地Epic目录? (.claude/epics/blog-system/)
  [Y/N] 删除工作树? (../epic-blog-system)
```

### `/pm:epic-edit` - 编辑Epic详情

**官方来源**: `.claude/commands/pm/epic-edit.md`

#### 命令语法
```bash
/pm:epic-edit <epic_name>
```

#### 功能说明
编辑Epic的实现方案，支持修改架构决策、技术方法和任务分解。

### `/pm:epic-refresh` - 刷新Epic进度

**官方来源**: `.claude/commands/pm/epic-refresh.md`

#### 命令语法
```bash
/pm:epic-refresh <epic_name>
```

#### 功能说明
从任务状态重新计算Epic的整体进度，同步GitHub Issue状态。

### `/pm:epic-oneshot` - 一键分解并同步

**官方来源**: `.claude/commands/pm/epic-oneshot.md`

#### 命令语法
```bash
/pm:epic-oneshot <feature_name>
```

#### 功能说明
组合执行 `/pm:epic-decompose` 和 `/pm:epic-sync`，适合确信Epic已就绪的情况。

#### 完整示例
```bash
# 一键完成分解和同步
/pm:epic-oneshot blog-system

# 等价于：
# /pm:epic-decompose blog-system
# /pm:epic-sync blog-system
```

---

## 第五阶段：并行执行开发

### `/pm:issue-analyze` - 分析任务并行化策略

**官方来源**: `.claude/commands/pm/issue-analyze.md`

#### 命令语法
```bash
/pm:issue-analyze <issue_number>
```

#### 功能说明
分析单个Issue，识别可并行的工作流，最大化开发效率。

#### 完整示例：分析数据库任务

```bash
# 1. 分析任务
/pm:issue-analyze 1234

# 系统会创建分析文件
```

**分析文件示例**（`.claude/epics/blog-system/1234-analysis.md`）:
```yaml
---
issue: 1234
title: "数据库Schema设计和迁移脚本"
analyzed_at: 2025-01-19T12:00:00Z
parallel_streams: 3
estimated_time_parallel: "2-3 hours"
estimated_time_sequential: "6-8 hours"
---

# Issue #1234 并行化分析

## 识别的并行工作流

### 工作流1：Schema设计 (schema-design)
**文件范围**: `models/`, `migrations/schema/`
**工作内容**:
- 设计表结构
- 定义关系和约束
- 创建基础model类

**预估时间**: 2小时
**依赖**: 无
**冲突风险**: 无

### 工作流2：迁移脚本 (migration-scripts)
**文件范围**: `migrations/versions/`, `alembic.ini`
**工作内容**:
- 创建Alembic配置
- 编写迁移脚本
- 测试迁移和回滚

**预估时间**: 2小时
**依赖**: Schema设计完成
**冲突风险**: 低

### 工作流3：测试数据 (test-data)
**文件范围**: `tests/fixtures/`, `seeds/`
**工作内容**:
- 创建测试数据
- 编写数据fixtures
- 性能测试数据

**预估时间**: 1小时
**依赖**: 迁移脚本完成
**冲突风险**: 无

## 并行化策略
### 推荐执行顺序
1. **Phase 1** (并行): Schema设计
2. **Phase 2** (串行): 迁移脚本（依赖Schema）
3. **Phase 3** (并行): 测试数据

## 建议的代理分配
- **Agent 1**: 专注Schema设计和Model定义
- **Agent 2**: 专注迁移脚本和Alembic配置
- **Agent 3**: 专注测试数据和Fixtures
```

### `/pm:epic-start` - 启动Epic并行执行

**官方来源**: `.claude/commands/pm/epic-start.md`

#### 命令语法
```bash
/pm:epic-start <epic_name>
```

#### 功能说明
启动整个Epic的并行代理执行，自动分析所有就绪的Issues并启动相应的工作流。

#### 执行状态文件示例
```yaml
---
epic: blog-system
status: in_progress
started_at: 2025-01-19T12:30:00Z
branch: epic/blog-system
worktree: ../epic-blog-system
active_agents: 3
---

# Blog System Epic 执行状态

## 当前活跃代理
### Agent 1: Database Schema
- **Issue**: #1234
- **工作流**: schema-design
- **状态**: active
- **进度**: 60%
- **预计完成**: 13:30

### Agent 2: User Authentication
- **Issue**: #1235
- **工作流**: auth-backend
- **状态**: active
- **进度**: 30%
- **预计完成**: 14:00

### Agent 3: Frontend Components
- **Issue**: #1236
- **工作流**: ui-components
- **状态**: active
- **进度**: 45%
- **预计完成**: 13:45

## 统计信息
- **总任务数**: 8
- **进行中**: 3
- **等待中**: 2
- **已完成**: 0
- **整体进度**: 25%
```

### `/pm:issue-start` - 启动单个任务

**官方来源**: `.claude/commands/pm/issue-start.md`

#### 命令语法
```bash
/pm:issue-start <issue_number>
```

#### 功能说明
基于工作流分析启动单个Issue的并行代理。如果没有分析文件，会自动进行分析。

---

## Worktree管理 - 独立并行开发

### Epic并行执行详解

**官方来源**: `.claude/commands/pm/epic-start.md`

CCPM的核心优势之一是支持在独立worktree中并行执行多个任务，避免代理间的上下文干扰。

#### Worktree创建和管理
```bash
# 启动Epic时自动创建worktree
/pm:epic-start blog-system

# Worktree位置: ../epic-blog-system
# 分支: epic/blog-system
# 独立工作目录，不影响主分支开发
```

#### 代理协调机制
- **文件级并行**: 不同代理处理不同文件，避免冲突
- **原子提交**: 每个代理频繁提交，格式`"Issue #1234: 具体更改"`
- **进度跟踪**: 实时更新到`.claude/epics/{epic}/updates/{issue}/stream-{X}.md`
- **依赖检查**: 自动检测任务完成并解锁依赖任务

#### 并行工作流示例
```
代理协调示例 - 博客系统开发:

Agent-1 (数据库专家):
  └─ Issue #1234: 数据库Schema
     ├─ Stream A: 设计表结构
     └─ Stream B: 编写迁移脚本

Agent-2 (后端专家):
  └─ Issue #1235: API端点
     ├─ Stream A: 用户认证API
     └─ Stream B: 文章管理API

Agent-3 (前端专家):
  └─ Issue #1236: UI组件
     ├─ Stream A: 基础组件库
     └─ Stream B: 页面布局

实时状态监控:
/pm:epic-show blog-system  # 查看整体进度
/pm:issue-show 1234        # 查看具体任务详情
```

### `/pm:issue-sync` - 同步Issue进度到GitHub

**官方来源**: `.claude/commands/pm/issue-sync.md`

#### 命令语法
```bash
/pm:issue-sync <issue_number>
```

#### 功能说明
将本地开发进度推送到GitHub作为Issue评论，建立透明的审计跟踪。

#### 前置条件
- GitHub CLI已认证 (`gh auth status`)
- Issue存在且可访问
- 本地更新目录存在 (`.claude/epics/*/updates/<issue_number>/`)
- 远程仓库不能是CCPM模板仓库

#### 核心特性
- **增量同步检测**: 只同步自上次sync后的新内容，防止重复评论
- **进度追踪**: 自动计算完成百分比并更新frontmatter
- **审计跟踪**: 维护同步时间戳用于审计
- **评论大小管理**: 处理GitHub 65,536字符限制，支持分割评论
- **Epic进度计算**: 任务完成时自动重新计算Epic进度

#### 详细使用示例
```bash
# 同步Issue #1235的最新进度
/pm:issue-sync 1235

# 系统会自动：
# 1. 检测自上次同步后的新更新
# 2. 计算当前完成百分比
# 3. 格式化进度报告
# 4. 推送到GitHub作为评论
# 5. 更新本地同步时间戳
```

#### 预期输出
```
✅ Issue同步完成: #1235
📊 进度: 75% (3/4 验收标准完成)
💬 GitHub评论: 已添加进度更新
⏰ 同步时间: 2024-01-19 14:30:00
🔄 Epic进度: 重新计算中...
```

### `/pm:issue-show` - 显示Issue详细信息

**官方来源**: `.claude/commands/pm/issue-show.md`

#### 命令语法
```bash
/pm:issue-show <issue_number>
```

#### 功能说明
显示Issue和相关子Issue的详细信息，包括GitHub状态和本地文件映射。

#### 核心特性
- **综合信息展示**: GitHub Issue详情 + 本地文件映射
- **关系展示**: 父Epic、依赖关系、阻塞关系、子任务
- **进度跟踪**: 验收标准状态显示
- **快速操作**: 提供常用命令快捷方式
- **最近活动**: 显示评论和更新历史

#### 详细使用示例
```bash
# 查看Issue详细信息
/pm:issue-show 1235
```

#### 预期输出格式
```
🎫 Issue #1235: 用户认证系统实现
   状态: 🔄 进行中
   标签: enhancement, backend, epic:blog-system
   负责人: Agent-1
   创建时间: 2024-01-19 10:00:00
   更新时间: 2024-01-19 14:15:00

📝 描述: 实现完整的用户注册、登录和权限管理功能
📁 本地文件: .claude/epics/blog-system/1235.md
🔗 相关Issues:
   ├─ 依赖: #1234 (数据库Schema) ✅ 已完成
   └─ 阻塞: #1238 (管理界面) ⏳ 等待中

💬 最近活动:
   - 14:15: 进度更新 - JWT认证完成
   - 13:30: 代理启动 - 开始实施

✅ 验收标准: (3/4 完成)
   ✅ 用户注册API端点
   ✅ 密码加密存储
   ✅ JWT令牌生成
   ⏳ 权限中间件实现

🚀 快速操作:
   /pm:issue-sync 1235    # 同步进度
   /pm:issue-start 1238   # 启动依赖任务
```

### `/pm:issue-status` - 检查Issue状态

**官方来源**: `.claude/commands/pm/issue-status.md`

#### 命令语法
```bash
/pm:issue-status <issue_number>
```

#### 功能说明
快速检查Issue的状态，包括进度、阻塞情况和下一步操作。

#### 使用示例
```bash
# 检查Issue状态
/pm:issue-status 1235
```

#### 预期输出格式
```
🎫 Issue #1235 状态概览

📊 进度: 75% (3/4 验收标准完成)
⏰ 状态: 🔄 进行中
🕐 最后更新: 30分钟前
👤 分配给: Agent-2

✅ 已完成:
  ✅ 用户注册API端点
  ✅ 密码加密存储
  ✅ JWT令牌生成

🔄 进行中:
  🔄 权限中间件实现 (预计30分钟完成)

⚠️ 阻塞情况: 无
🔗 依赖状态: 所有依赖已满足

🎯 下一步: /pm:issue-sync 1235
```

### `/pm:issue-close` - 关闭Issue

**官方来源**: `.claude/commands/pm/issue-close.md`

#### 命令语法
```bash
/pm:issue-close <issue_number>
```

#### 功能说明
标记Issue为完成状态，验证验收标准，并同步到GitHub。

#### 使用示例
```bash
# 关闭Issue
/pm:issue-close 1235
```

#### 预期输出
```
✅ Issue关闭: #1235 - 用户认证系统实现

📋 验收标准验证:
  ✅ 用户注册API端点 - 已验证
  ✅ 密码加密存储 - 已验证
  ✅ JWT令牌生成 - 已验证
  ✅ 权限中间件实现 - 已验证

🔄 GitHub同步:
  ✅ Issue #1235 已关闭
  ✅ Epic进度已更新 (80% 完成)

🎯 解锁任务:
  - Issue #1238 (管理界面) 现在可以开始
```

### `/pm:issue-reopen` - 重新打开Issue

**官方来源**: `.claude/commands/pm/issue-reopen.md`

#### 命令语法
```bash
/pm:issue-reopen <issue_number>
```

#### 功能说明
重新打开已关闭的Issue，适用于发现bug或需要补充功能的情况。

### `/pm:issue-edit` - 编辑Issue详情

**官方来源**: `.claude/commands/pm/issue-edit.md`

#### 命令语法
```bash
/pm:issue-edit <issue_number>
```

#### 功能说明
编辑Issue的描述、验收标准或其他详情信息。

---

## 第六阶段：状态跟踪和监控

### `/pm:status` - 整体项目状态

**官方来源**: `.claude/commands/pm/status.md`

#### 命令语法
```bash
/pm:status
```

#### 功能说明
显示所有项目的整体状态概览。

#### 示例输出
```
CCPM Project Status Overview
============================

📊 Active Epics: 2
🔄 In Progress Issues: 5
✅ Completed Today: 3
⏳ Blocked Issues: 1

## Epic: blog-system (Epic #1230)
Status: 🔄 In Progress (60% complete)
├── ✅ #1234: Database Schema (completed)
├── 🔄 #1235: User Authentication (75% - 30min remaining)
├── 🔄 #1236: Frontend Components (45% - 1hr remaining)
├── ⏳ #1237: API Endpoints (blocked - waiting for #1234)
└── 📋 #1238: Admin Interface (ready)

🎯 Recommended Next Actions:
1. Check progress on #1235 (User Authentication)
2. Prepare to start #1237 (API Endpoints)
3. Consider starting #1238 (Admin Interface) in parallel
```

### `/pm:epic-show` - 显示特定Epic详情

**官方来源**: `.claude/commands/pm/epic-show.md`

#### 命令语法
```bash
/pm:epic-show <epic_name>
```

#### 示例输出
```
Epic: blog-system
=================

📋 Basic Info:
- Name: blog-system
- Status: In Progress
- GitHub: https://github.com/user/repo/issues/1230
- Progress: 60% (3/5 tasks completed)
- Started: 2025-01-19 12:30
- Estimated Completion: 2025-01-20 16:00

📊 Task Breakdown:
┌─────────────────────────────────────┬──────────┬────────────┬─────────────┐
│ Task                                │ Status   │ Progress   │ Time Left   │
├─────────────────────────────────────┼──────────┼────────────┼─────────────┤
│ #1234: Database Schema              │ ✅ Done  │ 100%       │ -           │
│ #1235: User Authentication          │ 🔄 Active│ 75%        │ 30min       │
│ #1236: Frontend Components          │ 🔄 Active│ 45%        │ 1hr         │
│ #1237: API Endpoints                │ ⏳ Blocked│ 0%         │ Waiting     │
│ #1238: Admin Interface              │ 📋 Ready │ 0%         │ 2hrs        │
└─────────────────────────────────────┴──────────┴────────────┴─────────────┘

🚀 Active Agents:
- Agent 1: Working on User Authentication (#1235)
- Agent 2: Working on Frontend Components (#1236)

💡 Recommendations:
1. Focus resources on completing #1235 to unblock #1238
2. Consider starting #1237 as #1234 dependency is actually resolved
3. Review time estimates - some tasks consistently taking longer
```

### `/pm:next` - 智能下一步建议

**官方来源**: `.claude/commands/pm/next.md`

#### 命令语法
```bash
/pm:next
```

#### 功能说明
分析当前项目状态，提供智能的下一步行动建议。

#### 示例输出
```
🎯 Next Recommended Actions
===========================

## Immediate Actions (Next 1 hour)

### 1. 🔥 High Priority: Complete User Authentication
**Issue**: #1235 - User Authentication
**Reason**: Blocking other tasks (#1238)
**Action**: Check Agent 1 progress, provide assistance if needed
**Expected Impact**: Unblocks Admin Interface development

### 2. 🚀 Quick Win: Start API Endpoints
**Issue**: #1237 - API Endpoints
**Reason**: Dependency #1234 actually completed, but status not updated
**Action**: Run `/pm:issue-start 1237`
**Expected Impact**: Parallel progress while auth completes

## Resource Optimization
**Current Capacity**: 2/3 agents active (67% utilization)
**Recommendation**: Start #1237 to reach optimal 3/3 agent utilization
**Estimated Completion**: Tomorrow 16:00 → Tomorrow 14:30 (1.5hr savings)

🎯 **Suggested Next Command**: `/pm:issue-start 1237`
```

### `/pm:standup` - 每日站会报告

**官方来源**: `.claude/commands/pm/standup.md`

#### 命令语法
```bash
/pm:standup
```

#### 功能说明
生成每日站会报告，总结昨天完成的工作、今天的计划和遇到的阻塞。

#### 预期输出
```
📅 每日站会报告 - 2024-01-19

👥 团队状态:
  🔄 活跃代理: 3个
  ✅ 昨日完成: 2个任务
  🎯 今日计划: 3个任务

📈 昨日成果:
  ✅ #1234: 数据库Schema设计 - Agent-1 完成
  ✅ #1235: 用户认证API - Agent-2 完成

🚀 今日计划:
  🔄 #1236: 前端组件库 - Agent-3 (进行中, 70%)
  📋 #1237: API端点实现 - 待开始
  📋 #1238: 管理界面 - 等待依赖

⚠️ 阻塞和风险:
  🚨 #1237 需要等待 #1235 完全集成
  💡 建议: 优先完成 #1235 的集成测试

🎯 今日优先级:
  1. 完成 #1236 前端组件库
  2. 开始 #1237 API端点实现
  3. 准备 #1238 的开发环境
```

### `/pm:blocked` - 显示阻塞任务

**官方来源**: `.claude/commands/pm/blocked.md`

#### 命令语法
```bash
/pm:blocked
```

#### 功能说明
显示所有被阻塞的任务，分析阻塞原因并提供解决建议。

#### 预期输出
```
🚫 阻塞任务报告

📊 总览:
  - 被阻塞任务: 2个
  - 影响Epic: 1个
  - 预计延期: 1天

🚫 阻塞详情:

#1238: 管理界面实现
  🔗 阻塞原因: 依赖 #1235 (用户认证)
  ⏰ 阻塞时长: 2天
  💡 解决方案:
    - 完成 #1235 的权限中间件
    - 提供临时mock接口用于开发

#1240: 数据迁移脚本
  🔗 阻塞原因: 依赖 #1234 (数据库Schema)
  ⏰ 阻塞时长: 1天
  💡 解决方案: 已解决，可以开始

🎯 优先行动:
  1. /pm:issue-sync 1235  # 检查认证系统进度
  2. /pm:issue-start 1240 # 开始数据迁移脚本
```

### `/pm:in-progress` - 显示进行中工作

**官方来源**: `.claude/commands/pm/in-progress.md`

#### 命令语法
```bash
/pm:in-progress
```

#### 功能说明
显示所有进行中的工作，包括活跃代理和预计完成时间。

#### 预期输出
```
🔄 进行中工作概览

👥 活跃代理: 3个
📊 总体进度: 65%

🔄 进行中任务:

Agent-1: #1236 前端组件库
  📊 进度: 70%
  ⏰ 预计完成: 2小时
  🔧 当前工作: 实现表单验证组件

Agent-2: #1235 用户认证系统
  📊 进度: 90%
  ⏰ 预计完成: 30分钟
  🔧 当前工作: 权限中间件测试

Agent-3: #1237 API端点
  📊 进度: 45%
  ⏰ 预计完成: 3小时
  🔧 当前工作: 文章管理API实现

📈 今日预期完成:
  ✅ #1235 用户认证系统 (30分钟)
  ✅ #1236 前端组件库 (2小时)

⏳ 明日继续:
  🔄 #1237 API端点 (剩余55%)
```

---

## 上下文管理命令

### `/context:create` - 创建项目上下文

**官方来源**: `.claude/commands/context/create.md`

#### 命令语法
```bash
/context:create
```

#### 功能说明
分析项目结构并在 `.claude/context/` 目录中创建全面的基础文档。包括项目概览、架构、依赖关系和模式分析。

#### 使用场景
- 项目启动时创建初始上下文
- 上下文需要完全重建时

#### 输出内容
- 项目概览文档
- 架构分析文件
- 依赖关系映射
- 代码模式总结

### `/context:update` - 更新项目上下文

**官方来源**: `.claude/commands/context/update.md`

#### 命令语法
```bash
/context:update
```

#### 功能说明
基于最近的代码变更、新功能或架构更新刷新上下文文档。保留现有上下文的同时添加新信息。

#### 使用场景
- 重大变更后更新上下文
- 主要工作会话前同步状态

#### 输出结果
- 更新的上下文文件
- 变更跟踪记录

### `/context:prime` - 加载上下文到对话

**官方来源**: `.claude/commands/context/prime.md`

#### 命令语法
```bash
/context:prime
```

#### 功能说明
读取所有上下文文件并将其加载到当前对话的内存中。维护项目感知能力的关键操作。

#### 使用场景
- 任何工作会话开始时
- 需要完整项目理解时

#### 输出结果
- 上下文加载确认信息

---

## 测试管理命令

### `/testing:prime` - 配置测试环境

**官方来源**: `.claude/commands/testing/prime.md`

#### 命令语法
```bash
/testing:prime
```

#### 功能说明
检测并配置项目的测试框架，创建测试配置，并准备测试运行代理。

#### 使用场景
- 初始项目设置时
- 测试框架变更时

#### 输出文件
- `.claude/testing-config.md` - 包含测试命令和模式

#### 配置内容
- 测试框架识别
- 测试命令映射
- 测试模式定义

### `/testing:run` - 智能测试执行

**官方来源**: `.claude/commands/testing/run.md`

#### 命令语法
```bash
/testing:run [test_target]
```

#### 参数说明
- `test_target` (可选): 测试目标
  - 无参数: 运行所有测试
  - 文件路径: 运行特定测试文件
  - 模式: 运行匹配模式的测试

#### 功能说明
使用测试运行代理执行测试，该代理将输出记录到日志中，只向主线程返回关键结果以保持上下文简洁。

#### 执行特性
- 智能结果分析
- 失败案例详细诊断
- 上下文保护（详细输出不进入主对话）

#### 示例使用
```bash
# 运行所有测试
/testing:run

# 运行特定文件测试
/testing:run tests/test_auth.py

# 运行匹配模式的测试
/testing:run user_*
```

---

## 实用工具命令

### `/prompt` - 复杂提示处理

**官方来源**: `.claude/commands/utility/prompt.md`

#### 命令语法
```bash
# 先将复杂提示写入命令文件，然后执行：
/prompt
```

#### 功能说明
处理包含大量引用的复杂提示。当Claude界面拒绝复杂提示时，可以先将提示写入文件，然后通过此命令执行。

#### 使用场景
- Claude UI拒绝复杂提示时
- 包含大量 @ 引用的提示
- 需要预处理的复杂请求

#### 工作流程
1. 将复杂提示写入命令文件
2. 执行 `/prompt` 命令
3. 系统执行写入的提示

### `/re-init` - 重新初始化CLAUDE.md

**官方来源**: `.claude/commands/utility/re-init.md`

#### 命令语法
```bash
/re-init
```

#### 功能说明
使用 `.claude/CLAUDE.md` 中的规则更新项目根目录的 CLAUDE.md 文件，确保Claude实例获得正确的指令。

#### 使用场景
- 克隆PM系统后
- 更新规则后
- 确保Claude指令一致性

#### 输出结果
- 更新的项目根目录 CLAUDE.md 文件

---

## 代码审查命令

### `/code-rabbit` - CodeRabbit评论智能处理

**官方来源**: `.claude/commands/review/code-rabbit.md`

#### 命令语法
```bash
/code-rabbit
# 然后粘贴CodeRabbit评论内容
```

#### 功能说明
智能评估CodeRabbit建议，基于上下文感知接受有效改进，同时忽略缺乏上下文的建议。支持多文件审查的并行代理处理。

#### 智能评估特性
- **上下文感知**: 理解CodeRabbit缺乏完整上下文
- **接受标准**:
  - 真实的bug修复
  - 安全问题
  - 资源泄漏
- **忽略标准**:
  - 样式偏好
  - 无关模式建议

#### 处理能力
- 并行处理多文件审查
- 提供接受/忽略建议的理由说明

#### 输出结果
- 接受/忽略建议的摘要
- 每个决策的详细理由

---

## 命令设计模式

### 允许工具规范

每个命令在前言部分指定所需工具：
- `Read, Write, LS` - 文件操作
- `Bash` - 系统命令
- `Task` - 子代理生成
- `Grep` - 代码搜索

### 错误处理原则

命令遵循快速失败原则：
- 首先检查前置条件
- 提供清晰的错误信息和解决方案
- 绝不留下部分状态

### 上下文保护机制

处理大量信息的命令：
- 使用代理保护主线程免受冗长输出影响
- 返回摘要而非原始数据
- 仅保留关键信息

### 创建自定义命令

#### 命令文件结构
1. **创建文件**: `commands/category/command-name.md`
2. **添加前言**:
   ```yaml
   ---
   allowed-tools: Read, Write, LS
   ---
   ```
3. **内容结构**:
   - 目的和用法
   - 预检查项
   - 分步说明
   - 错误处理
   - 输出格式

#### 设计原则
- 保持简单（无过度验证）
- 快速失败，明确错误信息
- 使用代理处理重负载
- 返回简洁输出

### 代理集成机制

#### 四大核心代理类型

**官方来源**: 基于`.claude/agents/`目录分析

##### 1. file-analyzer (文件分析代理)
- **专长**: 日志分析、大文件摘要、错误诊断
- **使用场景**: 分析执行日志、提取关键信息
- **优势**: 减少上下文使用，提供精确摘要

##### 2. code-analyzer (代码分析代理)
- **专长**: 代码审查、漏洞检测、架构分析
- **使用场景**: 代码质量检查、逻辑跟踪
- **优势**: 深度代码理解，安全漏洞识别

##### 3. test-runner (测试执行代理)
- **专长**: 测试执行、结果分析、质量保证
- **使用场景**: 自动化测试、持续集成
- **优势**: 完整测试覆盖，详细错误报告

##### 4. parallel-worker (并行工作代理)
- **专长**: 多任务协调、并行执行管理
- **使用场景**: 大型Epic的并行开发
- **优势**: 避免上下文污染，提高执行效率

#### 代理调用最佳实践

```bash
# 分析复杂日志文件
使用 file-analyzer 代理处理大型日志

# 代码安全审查
使用 code-analyzer 代理检查潜在漏洞

# 执行完整测试套件
使用 test-runner 代理运行所有测试

# 启动并行开发
使用 parallel-worker 代理协调多任务
```

这样保持主对话上下文整洁的同时完成复杂工作。

### 命令执行说明

- 命令是被解释为指令的Markdown文件
- `/` 前缀触发命令执行
- 命令可以生成代理以保护上下文
- 所有PM命令（`/pm:*`）在主README中有文档
- 命令遵循 `/rules/` 中定义的规则

---

## 维护和同步命令

### `/pm:sync` - 双向同步

**官方来源**: `.claude/commands/pm/sync.md`

#### 命令语法
```bash
# 同步所有Epic
/pm:sync

# 同步特定Epic
/pm:sync <epic_name>
```

#### 功能说明
在本地文件和GitHub Issues之间进行完整的双向同步。

### `/pm:validate` - 验证系统状态

**官方来源**: `.claude/commands/pm/validate.md`

#### 命令语法
```bash
/pm:validate
```

#### 功能说明
检查CCPM系统的完整性和一致性。

#### 示例输出
```
CCPM System Validation
======================

✅ GitHub CLI: Installed and authenticated
✅ gh-sub-issue: Extension available
✅ Directory Structure: All required directories exist
✅ PRD Files: 2 valid PRDs found
✅ Epic Files: 2 epics, all valid
✅ Task Files: 12 tasks, all valid format

⚠️  Warnings:
- Epic 'blog-system' has 1 task with missing GitHub mapping
- 2 worktrees found but not referenced in active epics

❌ Errors:
- Task #1237: Invalid dependency reference (points to non-existent task)
- Epic 'old-project': Referenced GitHub issue not found

🔧 Suggested Fixes:
1. Run `/pm:sync blog-system` to fix GitHub mappings
2. Clean up orphaned worktrees with `/pm:clean`
3. Update dependency in task #1237 or create missing dependency task
```

### `/pm:import` - 导入现有GitHub Issues

**官方来源**: `.claude/commands/pm/import.md`

#### 命令语法
```bash
/pm:import
```

#### 功能说明
从GitHub导入现有的Issues，转换为本地CCPM格式，适用于迁移现有项目。

#### 使用场景
- 迁移现有项目到CCPM系统
- 同步外部创建的Issues
- 恢复意外删除的本地文件

#### 导入过程
```bash
# 启动导入向导
/pm:import

# 系统会扫描GitHub Issues并提供选择:
# 1. 全部导入
# 2. 按标签筛选导入
# 3. 按时间范围导入
# 4. 手动选择导入
```

### `/pm:search` - 搜索内容

**官方来源**: `.claude/commands/pm/search.md`

#### 命令语法
```bash
/pm:search <search_term>
```

#### 功能说明
在所有PRD、Epic和任务文件中搜索内容，支持正则表达式。

#### 使用示例
```bash
# 搜索关键字
/pm:search "用户认证"

# 搜索模式
/pm:search "API.*endpoint"
```

#### 预期输出
```
🔍 搜索结果: "用户认证" (共5个匹配)

📋 PRD文件:
  📄 blog-system.md:15 - 用户认证和权限管理
  📄 blog-system.md:89 - 用户认证API设计

📐 Epic文件:
  📄 blog-system/epic.md:23 - 用户认证架构决策
  📄 blog-system/epic.md:67 - 认证流程图

🎫 任务文件:
  📄 blog-system/1235.md:8 - 实现用户认证系统
```

### `/pm:clean` - 清理系统

**官方来源**: `.claude/commands/pm/clean.md`

#### 命令语法
```bash
/pm:clean
```

#### 功能说明
清理临时文件、无效状态和孤立的工作树。

#### 清理内容
- 已完成Epic的本地文件（可选）
- 孤立的工作树
- 临时缓存文件
- 无效的GitHub映射

#### 使用示例
```bash
# 执行系统清理
/pm:clean

# 交互式清理选项:
# [Y/N] 删除已完成Epic的本地文件?
# [Y/N] 清理孤立工作树?
# [Y/N] 重建GitHub映射缓存?
```

---

## 实战完整示例

### 完整项目流程演示

让我们通过一个完整的博客系统项目演示整个CCPM工作流程：

```bash
# === 第1步：系统初始化 ===
/pm:init
# ✅ GitHub CLI安装并认证
# ✅ 目录结构创建完成

# === 第2步：创建PRD ===
/pm:prd-new blog-system
# 📝 交互式PRD创建会话
# ✅ 创建文件：.claude/prds/blog-system.md

# === 第3步：PRD转技术方案 ===
/pm:prd-parse blog-system
# 🔧 技术架构分析
# ✅ 创建文件：.claude/epics/blog-system/epic.md

# === 第4步：一键分解并同步 ===
/pm:epic-oneshot blog-system
# 📋 Epic分解为5个任务
# 🔗 同步到GitHub Issues
# ✅ 创建工作树：../epic-blog-system

# === 第5步：并行开发执行 ===
/pm:epic-start blog-system
# 🚀 启动3个并行代理
# 📊 创建执行状态跟踪

# === 第6步：监控和调整 ===
/pm:status
# 📊 查看整体进度

/pm:epic-show blog-system
# 🔍 查看详细状态

/pm:next
# 🎯 获取下一步建议

# === 第7步：完成和清理 ===
/pm:sync blog-system
# 🔄 最终状态同步

/pm:validate
# ✅ 验证系统完整性
```

---

## 命令速查表

### 工作流程命令
| 命令 | 功能 | 示例 |
|------|------|------|
| `/pm:init` | 初始化系统 | `/pm:init` |
| `/pm:prd-new` | 创建PRD | `/pm:prd-new blog-system` |
| `/pm:prd-list` | 列出所有PRD | `/pm:prd-list` |
| `/pm:prd-edit` | 编辑PRD | `/pm:prd-edit blog-system` |
| `/pm:prd-status` | 显示PRD实施状态 | `/pm:prd-status blog-system` |
| `/pm:prd-parse` | PRD转Epic | `/pm:prd-parse blog-system` |
| `/pm:epic-decompose` | 分解任务 | `/pm:epic-decompose blog-system` |
| `/pm:epic-sync` | 同步GitHub | `/pm:epic-sync blog-system` |
| `/pm:epic-oneshot` | 一键处理 | `/pm:epic-oneshot blog-system` |
| `/pm:epic-list` | 列出所有Epic | `/pm:epic-list` |
| `/pm:epic-close` | 关闭Epic | `/pm:epic-close blog-system` |
| `/pm:epic-edit` | 编辑Epic详情 | `/pm:epic-edit blog-system` |
| `/pm:epic-refresh` | 刷新Epic进度 | `/pm:epic-refresh blog-system` |

### 上下文管理命令
| 命令 | 功能 | 示例 |
|------|------|------|
| `/context:create` | 创建项目上下文 | `/context:create` |
| `/context:update` | 更新项目上下文 | `/context:update` |
| `/context:prime` | 加载上下文到对话 | `/context:prime` |

### 测试管理命令
| 命令 | 功能 | 示例 |
|------|------|------|
| `/testing:prime` | 配置测试环境 | `/testing:prime` |
| `/testing:run` | 智能测试执行 | `/testing:run tests/test_auth.py` |

### 执行命令
| 命令 | 功能 | 示例 |
|------|------|------|
| `/pm:issue-analyze` | 分析任务 | `/pm:issue-analyze 1234` |
| `/pm:epic-start` | 启动Epic并行执行 | `/pm:epic-start blog-system` |
| `/pm:issue-start` | 启动单个任务 | `/pm:issue-start 1234` |
| `/pm:issue-sync` | 同步Issue进度 | `/pm:issue-sync 1234` |
| `/pm:issue-show` | 显示Issue详情 | `/pm:issue-show 1234` |
| `/pm:issue-status` | 检查Issue状态 | `/pm:issue-status 1234` |
| `/pm:issue-close` | 关闭Issue | `/pm:issue-close 1234` |
| `/pm:issue-reopen` | 重新打开Issue | `/pm:issue-reopen 1234` |
| `/pm:issue-edit` | 编辑Issue详情 | `/pm:issue-edit 1234` |

### 状态命令
| 命令 | 功能 | 示例 |
|------|------|------|
| `/pm:status` | 整体状态 | `/pm:status` |
| `/pm:epic-show` | Epic详情 | `/pm:epic-show blog-system` |
| `/pm:next` | 下一步建议 | `/pm:next` |
| `/pm:standup` | 每日站会报告 | `/pm:standup` |
| `/pm:blocked` | 显示阻塞任务 | `/pm:blocked` |
| `/pm:in-progress` | 显示进行中工作 | `/pm:in-progress` |

### 实用工具命令
| 命令 | 功能 | 示例 |
|------|------|------|
| `/prompt` | 复杂提示处理 | `/prompt` |
| `/re-init` | 重新初始化CLAUDE.md | `/re-init` |

### 代码审查命令
| 命令 | 功能 | 示例 |
|------|------|------|
| `/code-rabbit` | CodeRabbit评论智能处理 | `/code-rabbit` |

### 维护和调试命令
| 命令 | 功能 | 示例 |
|------|------|------|
| `/pm:sync` | 双向同步 | `/pm:sync blog-system` |
| `/pm:import` | 导入现有GitHub Issues | `/pm:import` |
| `/pm:search` | 搜索内容 | `/pm:search "用户认证"` |
| `/pm:validate` | 系统验证 | `/pm:validate` |
| `/pm:clean` | 清理系统 | `/pm:clean` |
| `/pm:test-reference-update` | 测试引用更新 | `/pm:test-reference-update` |
| `/pm:help` | 帮助信息 | `/pm:help` |

---

## 重要注意事项

### 命名规范
- **PRD和Epic名称**: 必须使用kebab-case（小写字母、数字、连字符）
- **分支命名**: 自动使用 `epic/<feature_name>` 格式
- **工作树**: 自动创建在 `../epic-<feature_name>`

### 依赖关系
- PRD必须在Epic创建前存在
- Epic必须在任务分解前存在
- 任务必须在GitHub同步前分解
- GitHub同步必须在并行执行前完成

### 文件结构
```
.claude/
├── prds/<feature>.md           # PRD文档
├── epics/<feature>/
│   ├── epic.md                 # Epic实现方案
│   ├── <issue_id>.md          # 任务文件
│   ├── <issue_id>-analysis.md # 任务分析
│   ├── execution-status.md    # 执行状态
│   └── updates/<issue_id>/    # 进度更新
│       └── stream-*.md        # 工作流进度
```

### 最佳实践
1. **PRD质量决定成败** - 投入充分时间完善PRD
2. **Epic目标10个以下任务** - 保持合理规模
3. **及时同步状态** - 定期运行 `/pm:sync`
4. **监控并行效率** - 使用 `/pm:status` 跟踪进度
5. **验证系统健康** - 定期运行 `/pm:validate`

---

**补充说明**: 本文档基于CCPM官方源码深度分析，涵盖了所有完整的命令系统和代理机制。确保信息的完整性和准确性。

**来源**: [CCPM GitHub仓库](https://github.com/automazeio/ccpm) - 基于官方命令定义文件验证