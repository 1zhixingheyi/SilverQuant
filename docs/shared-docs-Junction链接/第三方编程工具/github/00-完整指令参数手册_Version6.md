# 规范驱动编程工具完整指令参数手册

> 本手册用于速查和学习规范驱动开发工具的所有命令。每条命令都包含：**语法**、**参数**、**输入**、**输出**、**适用场景**、**简明示例**、**来源**、**注意事项**，便于日常开发实践查阅。

---

# Spec Kit - GitHub规范驱动开发框架

## 安装与初始化

### NPM 安装

- **语法**:  
  ```bash
  npm install -g @spec-kit/cli
  ```
- **参数**: 无
- **输入**: Node.js环境
- **输出**: 全局安装specify命令行工具
- **适用场景**: 推荐主安装方式
- **简明示例**:  
  ```bash
  npm install -g @spec-kit/cli
  ```
- **来源**: [npmjs.com/@spec-kit/cli](https://www.npmjs.com/package/@spec-kit/cli)

---

### pip 安装

- **语法**:  
  ```bash
  pip install spec-kit
  ```
- **参数**: 
  - `--user`（选填）: 用户级安装
  - `--upgrade`（选填）: 升级至最新版
- **输入**: Python 3.8+
- **输出**: 安装spec-kit命令行工具
- **适用场景**: Python环境推荐
- **简明示例**:  
  ```bash
  pip install spec-kit --user
  ```
- **来源**: [PyPI/spec-kit](https://pypi.org/project/spec-kit/)

---

### uvx 安装

- **语法**:  
  ```bash
  uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
  ```
- **参数**:  
  - `<PROJECT_NAME>`（必填）: 项目名称
- **输入**: 需要初始化的项目名
- **输出**: 拉取源码并初始化项目
- **适用场景**: 需从源码直接初始化
- **简明示例**:  
  ```bash
  uvx --from git+https://github.com/github/spec-kit.git specify init demo-proj
  ```
- **来源**: [GitHub官方仓库](https://github.com/github/spec-kit)

---

## 项目初始化与配置

### specify init

- **语法**:  
  ```bash
  specify init <PROJECT_NAME> [OPTIONS]
  ```
- **参数**:
  - `<PROJECT_NAME>`（必填）: 新项目目录名
  - `--ai`（选填，默认claude）: 指定AI类型
  - `--script`（选填）: 脚本类型，sh/ps
  - `--ignore-agent-tools`（选填）: 跳过AI代理检查
  - `--no-git`（选填）: 不初始化git仓库
  - `--here`（选填）: 当前目录初始化
  - `--github-token`（选填）: GitHub API令牌
- **输入**: 项目配置参数
- **输出**: 创建项目目录，生成`.specify/`配置
- **适用场景**: 规范驱动开发新项目起步
- **简明示例**:  
  ```bash
  specify init my-app --ai claude --script sh
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#specify-cli-reference)

---

### specify doctor

- **语法**:  
  ```bash
  specify doctor
  ```
- **参数**: 无
- **输入**: 系统环境
- **输出**: 工具链兼容性检查报告
- **适用场景**: 环境自检
- **简明示例**:  
  ```bash
  specify doctor
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#system-requirements)

---

### specify config

- **语法**:  
  ```bash
  specify config [show|edit|validate|export]
  ```
- **参数**:  
  - `show`：显示当前配置
  - `edit`：编辑配置
  - `validate`：校验配置
  - `export`：导出配置
- **输入**: 配置内容或编辑指令
- **输出**: `.specify/config.yml`变更
- **适用场景**: 项目配置管理
- **简明示例**:  
  ```bash
  specify config edit
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#configuration)

---

### specify upgrade

- **语法**:  
  ```bash
  specify upgrade [--preview] [--all] [--backup]
  ```
- **参数**:  
  - `--preview`：预览升级内容
  - `--all`：升级所有组件
  - `--backup`：升级前备份
- **输入**: 升级策略
- **输出**: 工具及规范模板更新
- **适用场景**: 项目/工具升级
- **简明示例**:  
  ```bash
  specify upgrade --all
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#upgrade)

---

### specify cleanup

- **语法**:  
  ```bash
  specify cleanup [--memory] [--temp] [--cache]
  ```
- **参数**:  
  - `--memory`：清理memory
  - `--temp`：清理临时文件
  - `--cache`：清理缓存
- **输入**: 清理类型
- **输出**: 释放磁盘和内存
- **适用场景**: 清理无用文件
- **简明示例**:  
  ```bash
  specify cleanup --cache
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#cleanup)

---

### specify remove

- **语法**:  
  ```bash
  specify remove [--preserve-memory] [--export-specs]
  ```
- **参数**:  
  - `--preserve-memory`：保留规范文档
  - `--export-specs`：导出规范定义
- **输入**: 保留策略
- **输出**: 卸载spec kit及相关文档
- **适用场景**: 项目去除spec kit
- **简明示例**:  
  ```bash
  specify remove --preserve-memory
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#removal)

---

### specify check

- **语法**:  
  ```bash
  specify check
  ```
- **参数**: 无
- **输入**: 系统环境
- **输出**: 依赖工具状态
- **适用场景**: 检查环境依赖
- **简明示例**:  
  ```bash
  specify check
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#specify-cli-reference)

---

## 规范驱动开发命令

### /constitution

- **语法**:  
  ```bash
  /constitution <原则说明>
  /constitution @file.md
  ```
- **参数**:  
  - `<原则说明>` 或 `@文件路径`
- **输入**: 项目治理原则与验收标准
- **输出**: `memory/constitution.md`
- **适用场景**: 明确项目治理、验收标准
- **简明示例**:  
  ```bash
  /constitution "本项目所有功能必须有自动化测试"
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#3-create-the-spec)

---

### /specify

- **语法**:  
  ```bash
  /specify "功能需求描述"
  ```
- **参数**:  
  - `"功能需求描述"`（必填）
- **输入**: 功能需求文本
- **输出**: `memory/`目录下技术规范文档
- **适用场景**: 需求转技术规范
- **简明示例**:  
  ```bash
  /specify "实现邮件验证码登录"
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#3-create-the-spec)

---

### /plan

- **语法**:  
  ```bash
  /plan
  ```
- **参数**: 无
- **输入**: `memory/`目录规范文档
- **输出**: `memory/plan.md`
- **适用场景**: 基于规范生成实施计划
- **简明示例**:  
  ```bash
  /plan
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#4-create-the-plan)

---

### /tasks

- **语法**:  
  ```bash
  /tasks
  ```
- **参数**: 无
- **输入**: `memory/plan.md`
- **输出**: `memory/tasks.md`任务与优先级
- **适用场景**: 计划分解为任务
- **简明示例**:  
  ```bash
  /tasks
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#5-create-the-tasks)

---

### /implement

- **语法**:  
  ```bash
  /implement
  ```
- **参数**: 无
- **输入**: `memory/tasks.md`
- **输出**: 逐步实施代码
- **适用场景**: 按任务自动实现
- **简明示例**:  
  ```bash
  /implement
  ```
- **来源**: [README.md](https://github.com/github/spec-kit#6-implement)

---

# Serena MCP - 语义代码分析工具

## 安装与初始化

### uv 安装

- **语法**:  
  ```bash
  uv add serena
  ```
- **参数**: 无
- **输入**: Python uv支持环境
- **输出**: serena依赖及命令行工具
- **适用场景**: 推荐方式
- **简明示例**:  
  ```bash
  uv add serena
  ```
- **来源**: [GitHub官方仓库](https://github.com/oraios/serena)

---

### cargo 安装

- **语法**:  
  ```bash
  cargo install serena
  ```
- **参数**:  
  - `--git <url>`（可选）: 指定源
  - `--features <features>`（可选）
  - `--force`（可选）
- **输入**: Rust环境
- **输出**: serena二进制
- **适用场景**: Rust用户
- **简明示例**:  
  ```bash
  cargo install serena
  ```
- **来源**: [README.md](https://github.com/oraios/serena)

---

## 配置/服务/分析

### serena config edit

- **语法**:  
  ```bash
  serena config edit [--directory <path>]
  ```
- **参数**:  
  - `--directory <path>`（可选）: 指定安装路径
- **输入**: 配置需求
- **输出**: `serena_config.yml`
- **适用场景**: 创建/编辑配置
- **简明示例**:  
  ```bash
  serena config edit
  ```
- **来源**: [README.md](https://github.com/oraios/serena#configuration)

---

### serena project generate-yml

- **语法**:  
  ```bash
  serena project generate-yml [--language <lang>]
  ```
- **参数**:  
  - `--language <lang>`（可选）: 主要语言
- **输入**: 项目信息
- **输出**: `.serena/project.yml`
- **适用场景**: 项目配置生成
- **简明示例**:  
  ```bash
  serena project generate-yml --language python
  ```
- **来源**: [README.md](https://github.com/oraios/serena#configuration)

---

### serena project index

- **语法**:  
  ```bash
  serena project index [--log-level <level>] [--timeout <seconds>]
  ```
- **参数**:  
  - `--log-level <level>`（可选）
  - `--timeout <seconds>`（可选）
- **输入**: 项目源码
- **输出**: 索引LSP缓存
- **适用场景**: 首次或大项目
- **简明示例**:  
  ```bash
  serena project index --log-level info
  ```
- **来源**: [README.md](https://github.com/oraios/serena#project-activation--indexing)

---

### serena start-mcp-server

- **语法**:  
  ```bash
  serena start-mcp-server [--project <name>] [--context <name>] [--mode <name>] [--transport <mode>] [--port <port>] [--directory <path>]
  ```
- **参数**:  
  - `--project <name>`（可选）
  - `--context <name>`（可选）
  - `--mode <name>`（可选）
  - `--transport stdio|streamable-http|sse`（可选, 默认stdio）
  - `--port <port>`（可选）
  - `--directory <path>`（可选）
- **输入**: 配置与环境
- **输出**: MCP服务启动
- **适用场景**: 代码分析服务
- **简明示例**:  
  ```bash
  serena start-mcp-server --transport streamable-http --port 8080
  ```
- **来源**: [README.md](https://github.com/oraios/serena#running-the-serena-mcp-server)

---

### serena tools list

- **语法**:  
  ```bash
  serena tools list [--only-optional] [--all] [--quiet]
  ```
- **参数**:  
  - `--only-optional`（可选）
  - `--all`（可选）
  - `--quiet`（可选）
- **输入**: 工具配置
- **输出**: 可用工具列表
- **适用场景**: 查看功能
- **简明示例**:  
  ```bash
  serena tools list --all
  ```
- **来源**: [README.md](https://github.com/oraios/serena#list-of-tools)

---

### serena health-check

- **语法**:  
  ```bash
  serena health-check [--detailed] [--repair]
  ```
- **参数**:  
  - `--detailed`（可选）
  - `--repair`（可选）
- **输入**: 环境与配置
- **输出**: 健康状态报告
- **适用场景**: 服务自检
- **简明示例**:  
  ```bash
  serena health-check --detailed
  ```
- **来源**: [README.md](https://github.com/oraios/serena#health-check)

---

### serena update-server

- **语法**:  
  ```bash
  serena update-server [--restart] [--backup]
  ```
- **参数**:  
  - `--restart`（可选）
  - `--backup`（可选）
- **输入**: 更新需求
- **输出**: 服务器升级
- **适用场景**: 服务升级
- **简明示例**:  
  ```bash
  serena update-server --restart
  ```
- **来源**: [README.md](https://github.com/oraios/serena#server-management)

---

### serena cleanup

- **语法**:  
  ```bash
  serena cleanup [--index] [--cache] [--logs] [--all]
  ```
- **参数**:  
  - `--index`（可选）
  - `--cache`（可选）
  - `--logs`（可选）
  - `--all`（可选）
- **输入**: 清理类型
- **输出**: 索引/缓存/日志清理
- **适用场景**: 空间与性能维护
- **简明示例**:  
  ```bash
  serena cleanup --all
  ```
- **来源**: [README.md](https://github.com/oraios/serena#cleanup)

---

### serena shutdown

- **语法**:  
  ```bash
  serena shutdown [--export-memories] [--backup-config]
  ```
- **参数**:  
  - `--export-memories`（可选）
  - `--backup-config`（可选）
- **输入**: 数据导出、备份
- **输出**: 服务停止、数据导出
- **适用场景**: 服务关机与迁移
- **简明示例**:  
  ```bash
  serena shutdown --export-memories
  ```
- **来源**: [README.md](https://github.com/oraios/serena#shutdown)

---

### MCP工具集（通过MCP协议）

- **常用命令**:  
  - `list_dir`：列目录
  - `find_file`：查找文件
  - `search_for_pattern`：代码文本搜索
  - `get_symbols_overview`：符号概览
  - `find_symbol`：查找符号定义
  - `replace_symbol_body`：替换函数/类内容
  - `write_memory/read_memory/list_memories/delete_memory`：AI辅助记忆管理
- **用法**: 通过MCP客户端或API调用，参数见官方文档
- **适用场景**: 代码分析、重构、导航、AI记忆等
- **来源**: [README.md MCP工具](https://github.com/oraios/serena#list-of-tools)
- **注意事项**: 详见MCP协议与官方工具集说明

---

# SuperClaude Framework - AI助手增强框架

## 安装与初始化

### NPM 安装

- **语法**:  
  ```bash
  npm install -g @superclaude-org/superclaude
  ```
- **参数**: 无
- **输入**: Node.js环境
- **输出**: 安装superclaude命令行
- **适用场景**: 推荐主安装方式
- **简明示例**:  
  ```bash
  npm install -g @superclaude-org/superclaude
  ```
- **来源**: [npmjs.com/@superclaude-org/superclaude](https://www.npmjs.com/package/@superclaude-org/superclaude)

---

### pip 安装

- **语法**:  
  ```bash
  pip install SuperClaude
  ```
- **参数**:  
  - `--extra-index-url <url>`（可选）
  - `--pre`（可选）
  - `--upgrade`（可选）
- **输入**: Python 3.9+
- **输出**: 安装SuperClaude
- **适用场景**: Python环境推荐
- **简明示例**:  
  ```bash
  pip install SuperClaude
  ```
- **来源**: [PyPI/SuperClaude](https://pypi.org/project/SuperClaude/)

---

## 系统检查/配置/升级/卸载

### /sc:system-check

- **语法**:  
  ```bash
  /sc:system-check [--comprehensive]
  ```
- **参数**:  
  - `--comprehensive`（可选）：深度系统检查
- **输入**: 系统资源和AI服务连接
- **输出**: 系统兼容性报告
- **适用场景**: 安装后或升级前检查
- **简明示例**:  
  ```bash
  /sc:system-check --comprehensive
  ```
- **来源**: [Docs/User-Guide/commands.md](https://github.com/SuperClaude-Org/SuperClaude_Framework/blob/master/Docs/User-Guide/commands.md#system-commands)

---

### /sc:config

- **语法**:  
  ```bash
  /sc:config [get|set|list|export|import] [key] [value]
  ```
- **参数**:  
  - `get <key>` 获取配置
  - `set <key> <value>` 设置配置
  - `list` 列出所有配置
  - `export <file>` 导出
  - `import <file>` 导入
- **输入**: 配置管理操作
- **输出**: 配置变更
- **适用场景**: 配置管理
- **简明示例**:  
  ```bash
  /sc:config set model claude-3
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:update

- **语法**:  
  ```bash
  /sc:update [--components|--agents|--check|--backup]
  ```
- **参数**:  
  - `--components` 更新核心
  - `--agents` 更新代理
  - `--check` 检查更新
  - `--backup` 备份
- **输入**: 更新策略
- **输出**: 升级结果
- **适用场景**: 框架升级
- **简明示例**:  
  ```bash
  /sc:update --agents
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:cache

- **语法**:  
  ```bash
  /sc:cache [clear|optimize|status] [--sessions|--models|--all]
  ```
- **参数**:  
  - `clear` 清理
  - `optimize` 优化
  - `status` 状态
  - `--sessions` 仅会话
  - `--models` 仅模型
  - `--all` 所有
- **输入**: 缓存管理指令
- **输出**: 缓存操作结果
- **适用场景**: 性能维护
- **简明示例**:  
  ```bash
  /sc:cache clear --all
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:uninstall

- **语法**:  
  ```bash
  /sc:uninstall [--preserve-sessions|--export-agents]
  ```
- **参数**:  
  - `--preserve-sessions` 保留会话
  - `--export-agents` 导出代理
- **输入**: 卸载策略
- **输出**: 卸载与数据导出
- **适用场景**: 框架卸载
- **简明示例**:  
  ```bash
  /sc:uninstall --export-agents
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

## AI开发/分析/设计/测试等核心命令

### /sc:brainstorm

- **语法**:  
  ```bash
  /sc:brainstorm "idea" [--strategy systematic|creative]
  ```
- **参数**:  
  - `"idea"`（必填）: 概念描述
  - `--strategy`（选填）: 思维模式
- **输入**: 需求/创意
- **输出**: 需求发现与建议
- **适用场景**: 需求收集、创新
- **简明示例**:  
  ```bash
  /sc:brainstorm "做一个AI语音助手" --strategy creative
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:implement

- **语法**:  
  ```bash
  /sc:implement "feature description" [--type frontend|backend|fullstack] [--focus security|performance]
  ```
- **参数**:  
  - `"feature description"`（必填）: 功能描述
  - `--type`（选填）: 类型
  - `--focus`（选填）: 关注点
- **输入**: 功能需求
- **输出**: 功能实现代码
- **适用场景**: 代码开发
- **简明示例**:  
  ```bash
  /sc:implement "用户注册接口" --type backend
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:analyze

- **语法**:  
  ```bash
  /sc:analyze [path] [--focus quality|security|performance|architecture]
  ```
- **参数**:  
  - `[path]`（选填）: 代码路径
  - `--focus`（选填）: 分析重点
- **输入**: 代码
- **输出**: 分析报告
- **适用场景**: 代码质量、安全等分析
- **简明示例**:  
  ```bash
  /sc:analyze src/ --focus security
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:test

- **语法**:  
  ```bash
  /sc:test [--type unit|integration|e2e] [--coverage] [--fix]
  ```
- **参数**:  
  - `--type` 测试类型
  - `--coverage` 覆盖率
  - `--fix` 自动修复
- **输入**: 测试配置
- **输出**: 测试报告
- **适用场景**: 质量保障
- **简明示例**:  
  ```bash
  /sc:test --type unit --coverage
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:improve

- **语法**:  
  ```bash
  /sc:improve [path] [--type performance|quality|security] [--preview]
  ```
- **参数**:  
  - `[path]`（选填）: 目标路径
  - `--type`（选填）: 优化类型
  - `--preview`（选填）: 预览
- **输入**: 代码
- **输出**: 优化建议或代码
- **适用场景**: 代码优化
- **简明示例**:  
  ```bash
  /sc:improve src/api --type performance
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:design

- **语法**:  
  ```bash
  /sc:design "system description" [--type api|database|ui|architecture]
  ```
- **参数**:  
  - `"system description"`（必填）: 系统描述
  - `--type`（选填）: 设计类型
- **输入**: 系统需求
- **输出**: 设计方案
- **适用场景**: 架构/系统设计
- **简明示例**:  
  ```bash
  /sc:design "CRM系统" --type architecture
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:workflow

- **语法**:  
  ```bash
  /sc:workflow "feature description" [--strategy agile|waterfall] [--format markdown]
  ```
- **参数**:  
  - `"feature description"`（必填）
  - `--strategy`（选填）
  - `--format`（选填）
- **输入**: 特性需求
- **输出**: 工作流计划
- **适用场景**: 项目实施计划
- **简明示例**:  
  ```bash
  /sc:workflow "开发电商结算模块" --strategy agile
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:estimate

- **语法**:  
  ```bash
  /sc:estimate "project scope" [--method story-points|hours|complexity] [--team-size number]
  ```
- **参数**:  
  - `"project scope"`（必填）
  - `--method`（选填）
  - `--team-size`（选填）
- **输入**: 需求与团队
- **输出**: 工作量与时间估算
- **适用场景**: 项目管理/评估
- **简明示例**:  
  ```bash
  /sc:estimate "开发API网关" --method hours --team-size 3
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:cleanup

- **语法**:  
  ```bash
  /sc:cleanup [path] [--type unused|duplicates|style|dependencies] [--aggressive]
  ```
- **参数**:  
  - `[path]`（选填）
  - `--type`（选填）
  - `--aggressive`（选填）
- **输入**: 代码/依赖
- **输出**: 技术债清理
- **适用场景**: 代码整理
- **简明示例**:  
  ```bash
  /sc:cleanup src/ --type unused --aggressive
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:document

- **语法**:  
  ```bash
  /sc:document [path] [--type api|user-guide|technical] [--format markdown|html]
  ```
- **参数**:  
  - `[path]`（选填）
  - `--type`（选填）
  - `--format`（选填）
- **输入**: 代码/结构
- **输出**: 文档生成
- **适用场景**: 自动化文档
- **简明示例**:  
  ```bash
  /sc:document src/ --type api --format markdown
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:task

- **语法**:  
  ```bash
  /sc:task "description" [--priority high|medium|low] [--delegate] [--track]
  ```
- **参数**:  
  - `"description"`（必填）
  - `--priority`（选填）
  - `--delegate`（选填）
  - `--track`（选填）
- **输入**: 任务需求
- **输出**: 任务跟踪与分配
- **适用场景**: 项目任务管理
- **简明示例**:  
  ```bash
  /sc:task "优化登录接口" --priority high --track
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:spawn

- **语法**:  
  ```bash
  /sc:spawn "project description" [--agents agent1,agent2] [--parallel] [--coordinate]
  ```
- **参数**:  
  - `"project description"`（必填）
  - `--agents`（选填）
  - `--parallel`（选填）
  - `--coordinate`（选填）
- **输入**: 大项目需求
- **输出**: 并行执行与协调
- **适用场景**: 大项目并行管理
- **简明示例**:  
  ```bash
  /sc:spawn "重构支付系统" --agents architect,devops --parallel
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:load

- **语法**:  
  ```bash
  /sc:load [context|@file] [--type project|session|knowledge] [--merge]
  ```
- **参数**:  
  - `[context|@file]`（选填）
  - `--type`（选填）
  - `--merge`（选填）
- **输入**: 上下文/文件
- **输出**: 上下文加载
- **适用场景**: 会话/项目载入
- **简明示例**:  
  ```bash
  /sc:load @project.md --type project
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:save

- **语法**:  
  ```bash
  /sc:save [name] [--type session|project|knowledge] [--include context,history,state]
  ```
- **参数**:  
  - `[name]`（选填）
  - `--type`（选填）
  - `--include`（选填）
- **输入**: 当前会话状态
- **输出**: 会话持久化
- **适用场景**: 项目/会话保存
- **简明示例**:  
  ```bash
  /sc:save v1 --type session --include context,history
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:reflect

- **语法**:  
  ```bash
  /sc:reflect [--scope session|task|project] [--validate] [--improve]
  ```
- **参数**:  
  - `--scope`（选填）
  - `--validate`（选填）
  - `--improve`（选填）
- **输入**: 当前状态
- **输出**: 评估与改进建议
- **适用场景**: 阶段性总结/复盘
- **简明示例**:  
  ```bash
  /sc:reflect --scope task --validate
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:help

- **语法**:  
  ```bash
  /sc:help [command]
  ```
- **参数**: `[command]`（选填）
- **输入**: 帮助查询
- **输出**: 命令描述
- **适用场景**: 指令速查
- **简明示例**:  
  ```bash
  /sc:help /sc:task
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:index

- **语法**:  
  ```bash
  /sc:index [target] [--type docs|api|structure|readme] [--format md|json|yaml]
  ```
- **参数**:  
  - `[target]`（选填）
  - `--type`（选填）
  - `--format`（选填）
- **输入**: 文件/项目
- **输出**: 项目结构知识库
- **适用场景**: 文档/API自动索引
- **简明示例**:  
  ```bash
  /sc:index src/ --type api --format yaml
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### /sc:debug

- **语法**:  
  ```bash
  /sc:debug "问题描述" [--context file1,file2] [--strategy systematic|hypothesis|binary]
  ```
- **参数**:  
  - `"问题描述"`（必填）
  - `--context`（选填）
  - `--strategy`（选填）
- **输入**: 问题现象、相关代码
- **输出**: 调试建议与分析
- **适用场景**: 难题排查
- **简明示例**:  
  ```bash
  /sc:debug "接口500错误" --context api.py --strategy hypothesis
  ```
- **来源**: [Docs/User-Guide/commands.md]

---

### 专业代理指令（@agent-*）

- **语法**:  
  ```bash
  @agent-类型 "任务描述"
  ```
- **常用类型**:  
  - system-architect
  - backend-architect
  - frontend-architect
  - devops-architect
  - security-engineer
  - performance-engineer
  - quality-engineer
  - refactoring-expert
  - python-expert
  - requirements-analyst
  - root-cause-analyst
  - technical-writer
  - learning-guide
  - socratic-mentor
- **输入**: 任务描述
- **输出**: 对应专业建议
- **适用场景**: 各专业领域专家级AI助理
- **简明示例**:  
  ```bash
  @agent-system-architect "设计高可用微服务架构"
  ```
- **来源**: [Docs/User-Guide/agents.md](https://github.com/SuperClaude-Org/SuperClaude_Framework/blob/master/Docs/User-Guide/agents.md)

---

**最后更新**: 2025-09-20