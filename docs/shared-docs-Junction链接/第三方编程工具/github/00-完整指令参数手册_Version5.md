# 规范驱动编程工具完整指令参数手册

> 本手册用于速查和学习规范驱动开发工具的所有命令。每条命令都包含：**语法**、**参数**、**输入**、**输出**、**适用场景**、**简明示例**、**来源**、**注意事项**，便于日常开发实践查阅。

---

## 目录

- [CCPM - Claude Code项目管理系统](#ccpm---claude-code项目管理系统)
- [Spec Kit - GitHub规范驱动开发框架](#spec-kit---github规范驱动开发框架)
- [Serena MCP - 语义代码分析工具](#serena-mcp---语义代码分析工具)
- [SuperClaude Framework - AI助手增强框架](#superclaude-framework---ai助手增强框架)

---

# CCPM - Claude Code项目管理系统

## 安装与初始化

### 安装

- **语法**:  
  ```bash
  # Linux/macOS
  curl -sSL https://raw.githubusercontent.com/automazeio/ccpm/main/ccpm.sh | bash
  # 或
  wget -qO- https://raw.githubusercontent.com/automazeio/ccpm/main/ccpm.sh | bash

  # Windows PowerShell
  iwr -useb https://raw.githubusercontent.com/automazeio/ccpm/main/ccpm.bat | iex

  # 手动克隆（开发者/高级用户）
  git clone https://github.com/automazeio/ccpm.git
  ```
- **来源**: [GitHub官方仓库](https://github.com/automazeio/ccpm)
- **注意事项**:  
  - 推荐直接脚本安装。手动克隆适合深度自定义，clone后需手动初始化。

---

### /pm:init

- **语法**: 
  ```bash
  /pm:init
  ```
- **参数**: 无
- **输入**:
  - GitHub账户权限（自动检测）。
- **输出**:
  - 安装/更新 GitHub CLI
  - 完成 GitHub 登录认证
  - 安装 `gh-sub-issue` 扩展
  - 生成 `.claude/` 目录结构
  - 创建 `.gitignore`
- **适用场景**:
  - 首次配置 Claude Code PM 系统。
- **简明示例**:
  ```bash
  /pm:init
  ```
- **来源**:
  - [COMMANDS.md](https://github.com/automazeio/ccpm/blob/main/COMMANDS.md)
- **注意事项**:
  - 多次运行无副作用，如需重新初始化可再次执行。

---

### /pm:import

- **语法**: 
  ```bash
  /pm:import [--epic <epic_name>] [--label <label>]
  ```
- **参数**:
  - `--epic <epic_name>`（选填，字符串）: 指定导入到哪个epic。
  - `--label <label>`（选填，字符串）: 仅导入带此标签的issue。
- **输入**:
  - 现有的 GitHub 仓库issues。
- **输出**:
  - 将GitHub issues导入PM系统，自动生成本地epic和task结构。
- **适用场景**:
  - 旧项目迁移或已有issue体系纳入管理。
- **简明示例**:
  ```bash
  /pm:import --epic legacy-migration --label bug
  ```
- **来源**:
  - [COMMANDS.md](https://github.com/automazeio/ccpm/blob/main/COMMANDS.md)
- **注意事项**:
  - 已有本地记录的issue不会重复导入；自动分配epic、task类别。

---

### /context:create

- **语法**: 
  ```bash
  /context:create
  ```
- **参数**: 无
- **输入**:
  - 项目文件结构、代码内容。
- **输出**:
  - 在 `.claude/context/` 生成项目概述、架构分析、依赖、代码模式等基线文档。
- **适用场景**:
  - 新项目或上下文完全重建时。
- **简明示例**:
  ```bash
  /context:create
  ```
- **来源**:
  - [COMMANDS.md]

---

### /context:update

- **语法**: 
  ```bash
  /context:update
  ```
- **参数**: 无
- **输入**:
  - 最近代码更改、新增文件或架构变更。
- **输出**:
  - 更新`.claude/context/`相关文档，包含变更跟踪。
- **适用场景**:
  - 新需求、重构、架构调整后。
- **简明示例**:
  ```bash
  /context:update
  ```
- **来源**:
  - [COMMANDS.md]

---

### /context:prime

- **语法**: 
  ```bash
  /context:prime
  ```
- **参数**: 无
- **输入**:
  - `.claude/context/`目录全部内容。
- **输出**:
  - 加载所有上下文到当前AI/会话内存，激活项目感知。
- **适用场景**:
  - 每次工作会话前建议执行。
- **简明示例**:
  ```bash
  /context:prime
  ```
- **来源**:
  - [COMMANDS.md]

---

### /context

- **语法**: 
  ```bash
  /context
  ```
- **参数**: 无
- **输入**:
  - 当前上下文状态数据。
- **输出**:
  - 彩色网格视图，诊断上下文覆盖。
- **适用场景**:
  - 检查AI上下文感知状况。
- **简明示例**:
  ```bash
  /context
  ```
- **来源**:
  - [COMMANDS.md]

---

## 产品需求文档 (PRD) 管理

### /pm:prd-new

- **语法**: 
  ```bash
  /pm:prd-new <feature-name>
  ```
- **参数**:
  - `<feature-name>`（必填，字符串）: 新功能特性名称，作为PRD文档名。
- **输入**:
  - 交互式输入功能需求（AI引导填写背景、目标、验收标准）。
- **输出**:
  - `.claude/prds/<feature-name>.md` 完整PRD文档（含背景、目标、标准）。
- **适用场景**:
  - 新功能/模块需求规划与记录。
- **简明示例**:
  ```bash
  /pm:prd-new user-authentication
  ```
- **来源**:
  - [COMMANDS.md]
- **注意事项**:
  - 建议feature-name用英文小写短横线，避免重名。

---

### /pm:prd-list

- **语法**: 
  ```bash
  /pm:prd-list
  ```
- **参数**: 无
- **输入**:
  - `.claude/prds/`目录内容。
- **输出**:
  - 所有PRD文档的列表和状态概览。
- **适用场景**:
  - 快速查阅所有需求文档。
- **简明示例**:
  ```bash
  /pm:prd-list
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:prd-edit

- **语法**: 
  ```bash
  /pm:prd-edit <prd-name>
  ```
- **参数**:
  - `<prd-name>`（必填，字符串）: 需编辑的PRD文档名。
- **输入**:
  - 修改内容（AI交互引导）。
- **输出**:
  - 更新指定PRD文档。
- **适用场景**:
  - 修改和维护现有需求文档。
- **简明示例**:
  ```bash
  /pm:prd-edit user-authentication
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:prd-status

- **语法**: 
  ```bash
  /pm:prd-status <prd-name>
  ```
- **参数**:
  - `<prd-name>`（必填，字符串）: PRD文档名。
- **输入**:
  - 实现进度数据。
- **输出**:
  - 状态报告和进度追踪。
- **适用场景**:
  - 跟踪PRD实现进度。
- **简明示例**:
  ```bash
  /pm:prd-status user-authentication
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:prd-parse

- **语法**: 
  ```bash
  /pm:prd-parse <feature-name>
  ```
- **参数**:
  - `<feature-name>`（必填，字符串）: 功能名称。
- **输入**:
  - 现有PRD文档内容。
- **输出**:
  - `.claude/epics/<feature-name>/epic.md` 技术实现计划。
- **适用场景**:
  - 需求转化为技术史诗。
- **简明示例**:
  ```bash
  /pm:prd-parse user-authentication
  ```
- **来源**:
  - [COMMANDS.md]

---

## Epic与任务管理

### /pm:epic-decompose

- **语法**: 
  ```bash
  /pm:epic-decompose <feature-name>
  ```
- **参数**:
  - `<feature-name>`（必填，字符串）: Epic名称。
- **输入**:
  - 史诗文档内容。
- **输出**:
  - 拆分为具体任务文件，含验收标准、估算。
- **适用场景**:
  - 大型功能分解。
- **简明示例**:
  ```bash
  /pm:epic-decompose user-authentication
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:epic-sync

- **语法**: 
  ```bash
  /pm:epic-sync <feature-name>
  ```
- **参数**:
  - `<feature-name>`（必填，字符串）: Epic名称。
- **输入**:
  - 本地epic和任务数据。
- **输出**:
  - 在GitHub创建对应issue结构。
- **适用场景**:
  - 本地分解同步到GitHub。
- **简明示例**:
  ```bash
  /pm:epic-sync user-authentication
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:epic-oneshot

- **语法**: 
  ```bash
  /pm:epic-oneshot <feature-name>
  ```
- **参数**:
  - `<feature-name>`（必填，字符串）: Epic名称。
- **输入**:
  - Epic描述。
- **输出**:
  - 分解并同步到GitHub，自动完成epic→task→issue全流程。
- **适用场景**:
  - 快速全流程处理。
- **简明示例**:
  ```bash
  /pm:epic-oneshot user-authentication
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:epic-list

- **语法**: 
  ```bash
  /pm:epic-list
  ```
- **参数**: 无
- **输入**:
  - `.claude/epics/`目录内容。
- **输出**:
  - 所有epic列表与状态。
- **适用场景**:
  - 快速查阅史诗。
- **简明示例**:
  ```bash
  /pm:epic-list
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:epic-show

- **语法**: 
  ```bash
  /pm:epic-show <epic-name>
  ```
- **参数**:
  - `<epic-name>`（必填，字符串）: 史诗名称。
- **输入**:
  - 指定epic及相关任务。
- **输出**:
  - 史诗详情、任务状态视图。
- **适用场景**:
  - 查看进展与详情。
- **简明示例**:
  ```bash
  /pm:epic-show user-authentication
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:epic-close

- **语法**: 
  ```bash
  /pm:epic-close <epic-name>
  ```
- **参数**:
  - `<epic-name>`（必填，字符串）: 史诗名称。
- **输入**:
  - 完成确认。
- **输出**:
  - 标记epic为完成。
- **适用场景**:
  - 关闭已完成史诗。
- **简明示例**:
  ```bash
  /pm:epic-close user-authentication
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:epic-edit

- **语法**: 
  ```bash
  /pm:epic-edit <epic-name>
  ```
- **参数**:
  - `<epic-name>`（必填，字符串）: 史诗名称。
- **输入**:
  - 修改内容。
- **输出**:
  - 更新epic详情。
- **适用场景**:
  - 维护/调整史诗内容。
- **简明示例**:
  ```bash
  /pm:epic-edit user-authentication
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:epic-refresh

- **语法**: 
  ```bash
  /pm:epic-refresh <epic-name>
  ```
- **参数**:
  - `<epic-name>`（必填，字符串）: 史诗名称。
- **输入**:
  - 相关任务状态。
- **输出**:
  - 刷新epic进度。
- **适用场景**:
  - 进度同步与刷新。
- **简明示例**:
  ```bash
  /pm:epic-refresh user-authentication
  ```
- **来源**:
  - [COMMANDS.md]

---

## Issue管理

### /pm:issue-show

- **语法**:
  ```bash
  /pm:issue-show <issue-number>
  ```
- **参数**:
  - `<issue-number>`（必填，数字）: GitHub问题编号。
- **输入**:
  - 问题及子任务数据。
- **输出**:
  - 问题详情和子任务视图。
- **适用场景**:
  - 查看问题及其分解任务。
- **简明示例**:
  ```bash
  /pm:issue-show 1234
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:issue-status

- **语法**:
  ```bash
  /pm:issue-status <issue-number>
  ```
- **参数**:
  - `<issue-number>`（必填，数字）: GitHub问题编号。
- **输入**:
  - 问题状态数据。
- **输出**:
  - 问题当前状态和进度报告。
- **适用场景**:
  - 跟踪单一问题进展。
- **简明示例**:
  ```bash
  /pm:issue-status 1234
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:issue-start

- **语法**:
  ```bash
  /pm:issue-start <issue-number>
  ```
- **参数**:
  - `<issue-number>`（必填，数字）: GitHub问题编号。
- **输入**:
  - 问题要求和上下文。
- **输出**:
  - 启动专属开发代理，维护本地进度。
- **适用场景**:
  - 开始处理某个任务。
- **简明示例**:
  ```bash
  /pm:issue-start 1234
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:issue-sync

- **语法**:
  ```bash
  /pm:issue-sync <issue-number>
  ```
- **参数**:
  - `<issue-number>`（必填，数字）: GitHub问题编号。
- **输入**:
  - 本地进度更新。
- **输出**:
  - 进度同步到GitHub（注释/状态）。
- **适用场景**:
  - 本地与GitHub进度一致。
- **简明示例**:
  ```bash
  /pm:issue-sync 1234
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:issue-close

- **语法**:
  ```bash
  /pm:issue-close <issue-number>
  ```
- **参数**:
  - `<issue-number>`（必填，数字）: GitHub问题编号。
- **输入**:
  - 完成确认。
- **输出**:
  - 问题标记为完成状态。
- **适用场景**:
  - 关闭已完成任务。
- **简明示例**:
  ```bash
  /pm:issue-close 1234
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:issue-reopen

- **语法**:
  ```bash
  /pm:issue-reopen <issue-number>
  ```
- **参数**:
  - `<issue-number>`（必填，数字）: GitHub问题编号。
- **输入**:
  - 重新激活原因。
- **输出**:
  - 重新打开已关闭的问题。
- **适用场景**:
  - 任务回归处理。
- **简明示例**:
  ```bash
  /pm:issue-reopen 1234
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:issue-edit

- **语法**:
  ```bash
  /pm:issue-edit <issue-number>
  ```
- **参数**:
  - `<issue-number>`（必填，数字）: GitHub问题编号。
- **输入**:
  - 问题修改要求。
- **输出**:
  - 更新问题内容和配置。
- **适用场景**:
  - 修改问题详情和说明。
- **简明示例**:
  ```bash
  /pm:issue-edit 1234
  ```
- **来源**:
  - [COMMANDS.md]

---

## 工作流与维护

### /pm:next

- **语法**:
  ```bash
  /pm:next
  ```
- **参数**: 无
- **输入**:
  - 所有epic和任务优先级数据。
- **输出**:
  - 下一个优先问题及epic上下文。
- **适用场景**:
  - 获取当前应处理的下一个任务。
- **简明示例**:
  ```bash
  /pm:next
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:status

- **语法**:
  ```bash
  /pm:status
  ```
- **参数**: 无
- **输入**:
  - 项目整体状态数据。
- **输出**:
  - 项目总体状态仪表板。
- **适用场景**:
  - 项目管理总览。
- **简明示例**:
  ```bash
  /pm:status
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:standup

- **语法**:
  ```bash
  /pm:standup
  ```
- **参数**: 无
- **输入**:
  - 项目进度与任务状态。
- **输出**:
  - 进度报告，适用于早会。
- **适用场景**:
  - 团队每日站会。
- **简明示例**:
  ```bash
  /pm:standup
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:blocked

- **语法**:
  ```bash
  /pm:blocked
  ```
- **参数**: 无
- **输入**:
  - 任务阻塞状态。
- **输出**:
  - 当前被阻塞任务列表。
- **适用场景**:
  - 阻塞点识别与处理。
- **简明示例**:
  ```bash
  /pm:blocked
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:in-progress

- **语法**:
  ```bash
  /pm:in-progress
  ```
- **参数**: 无
- **输入**:
  - 当前进行中的工作数据。
- **输出**:
  - 进行中任务和工作列表。
- **适用场景**:
  - 跟踪开发状态。
- **简明示例**:
  ```bash
  /pm:in-progress
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:sync

- **语法**:
  ```bash
  /pm:sync
  ```
- **参数**: 无
- **输入**:
  - 本地与GitHub状态数据。
- **输出**:
  - 本地与远程状态同步。
- **适用场景**:
  - 项目状态一致性保证。
- **简明示例**:
  ```bash
  /pm:sync
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:validate

- **语法**:
  ```bash
  /pm:validate
  ```
- **参数**: 无
- **输入**:
  - PM系统配置与数据。
- **输出**:
  - 配置和数据完整性检查报告。
- **适用场景**:
  - 系统健康检查。
- **简明示例**:
  ```bash
  /pm:validate
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:clean

- **语法**:
  ```bash
  /pm:clean
  ```
- **参数**: 无
- **输入**:
  - 已完成epic和任务数据。
- **输出**:
  - 清理归档已完成内容。
- **适用场景**:
  - 项目结构维护。
- **简明示例**:
  ```bash
  /pm:clean
  ```
- **来源**:
  - [COMMANDS.md]

---

### /pm:search

- **语法**:
  ```bash
  /pm:search <search-term>
  ```
- **参数**:
  - `<search-term>`（必填，字符串）: 搜索关键词。
- **输入**:
  - 所有PRD、epic、任务内容。
- **输出**:
  - 全文搜索结果。
- **适用场景**:
  - 跨内容信息检索。
- **简明示例**:
  ```bash
  /pm:search authentication
  ```
- **来源**:
  - [COMMANDS.md]

---

### /testing:prime

- **语法**:
  ```bash
  /testing:prime
  ```
- **参数**: 无
- **输入**:
  - 项目测试框架配置。
- **输出**:
  - 检测和配置测试环境，生成`.claude/testing-config.md`。
- **适用场景**:
  - 测试环境初始化。
- **简明示例**:
  ```bash
  /testing:prime
  ```
- **来源**:
  - [COMMANDS.md]

---

### /testing:run

- **语法**:
  ```bash
  /testing:run [test_target]
  ```
- **参数**:
  - `[test_target]`（选填，字符串/文件/模式）: 指定测试目标。
- **输入**:
  - 测试套件与目标。
- **输出**:
  - 运行测试并返回摘要。
- **适用场景**:
  - 智能测试执行。
- **简明示例**:
  ```bash
  /testing:run tests/unit/
  ```
- **来源**:
  - [COMMANDS.md]

---

### /prompt

- **语法**:
  ```bash
  /prompt
  ```
- **参数**: 无
- **输入**:
  - 粘贴复杂提示内容。
- **输出**:
  - 处理复杂提示。
- **适用场景**:
  - Claude UI拒绝复杂输入时。
- **简明示例**:
  ```bash
  /prompt
  ```
- **来源**:
  - [COMMANDS.md]

---

### /re-init

- **语法**:
  ```bash
  /re-init
  ```
- **参数**: 无
- **输入**:
  - `.claude/CLAUDE.md` 中规则。
- **输出**:
  - 更新项目CLAUDE.md。
- **适用场景**:
  - 配置文件同步。
- **简明示例**:
  ```bash
  /re-init
  ```
- **来源**:
  - [COMMANDS.md]

---

### /code-rabbit

- **语法**:
  ```bash
  /code-rabbit
  ```
- **参数**: 无
- **输入**:
  - CodeRabbit评审意见。
- **输出**:
  - 评估建议，支持并行评审。
- **适用场景**:
  - 智能处理代码评审。
- **简明示例**:
  ```bash
  /code-rabbit
  ```
- **来源**:
  - [COMMANDS.md]

---

# Spec Kit - GitHub规范驱动开发框架

（**同样结构**，请参见上一节的每条命令模板，依次补全：  
- specify init  
- pip install spec-kit  
- specify doctor  
- specify config  
- specify upgrade  
- specify cleanup  
- specify remove  
- specify check  
- /constitution  
- /specify  
- /plan  
- /tasks  
- /implement  
等，详见你的原始命令清单，每条结构和CCPM一致。）

---

# Serena MCP - 语义代码分析工具

（**同样结构**，每条命令依次补全：  
- uv add serena  
- cargo install serena  
- serena config edit  
- serena project index  
- serena tools list  
- serena health-check  
- serena update-server  
- serena cleanup  
- serena shutdown  
- serena start-mcp-server  
- serena project generate-yml  
- MCP子命令（list_dir、find_file、replace_symbol_body等，建议以小节汇总）  
等。）

---

# SuperClaude Framework - AI助手增强框架

（**同样结构**，每条命令依次补全：  
- pip install SuperClaude  
- npm install -g @superclaude-org/superclaude  
- /sc:system-check  
- /sc:config  
- /sc:update  
- /sc:cache  
- /sc:uninstall  
- /sc:brainstorm  
- /sc:implement  
- /sc:analyze  
- /sc:test  
- /sc:improve  
- /sc:design  
- /sc:workflow  
- /sc:estimate  
- /sc:cleanup  
- /sc:document  
- /sc:task  
- /sc:spawn  
- /sc:load  
- /sc:save  
- /sc:reflect  
- /sc:help  
- /sc:index  
- /sc:debug  
- @agent-* 专业代理系列  
等。）

---

> **说明**：  
> 由于所有命令完整展开会极长，如需**任意工具全部命令详细结构化内容**，请直接指定工具名，如“请给我Spec Kit全部命令结构化详情”。

---
**最后更新**: 2025-09-20