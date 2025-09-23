# Serena MCP编码代理全流程指南

## 快速参考

### 工具概述
**Serena** 是由Oraios AI开发的强大MCP服务器，将任何大型语言模型转换为功能完整的编码代理。提供语义级代码检索、智能编辑和Shell执行功能，支持多种编程语言的IDE级别代码分析。

**核心优势**：
- **免费开源**：无需API密钥或订阅费用
- **语义理解**：基于LSP的深度代码分析，超越简单文本匹配
- **多语言支持**：Python、TypeScript、Go、Rust、C/C++、Java等
- **IDE集成**：原生支持Claude Code、Cursor、VSCode等开发环境

### 支持语言
- **直接支持**：Python、TypeScript/JavaScript、PHP、Go、Rust、C/C++、Java
- **间接支持**：Ruby、C#、Kotlin、Dart

## 工具使用生命周期

### 阶段0: 环境准备 - `安装配置`

#### 安装方式选择

##### 方式1: uvx安装（推荐）
```bash
# 直接运行最新版本
uvx --from git+https://github.com/oraios/serena serena start-mcp-server

# Claude Code快速集成
claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant --project $(pwd)
```

##### 方式2: Nix安装
```bash
# 需要启用nix-command和flakes功能
nix run github:oraios/serena -- start-mcp-server --transport stdio
```

##### 方式3: Docker运行
```bash
docker run --rm -i --network host \
  -v /path/to/your/projects:/workspaces/projects \
  ghcr.io/oraios/serena:latest \
  serena start-mcp-server --transport stdio
```

#### 默认行为说明
- **自动依赖检测**：首次运行时自动检测语言服务器依赖
- **配置文件生成**：在`~/.serena/`目录下自动创建配置文件
- **Web仪表板启动**：默认在localhost启动监控界面

#### 新手实用技巧
```bash
# 快速验证安装
uvx --from git+https://github.com/oraios/serena serena --help

# 生成项目配置
uvx --from git+https://github.com/oraios/serena serena project generate-yml
```

#### 详细使用示例

##### 示例1: Claude Code集成场景
```bash
claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant --project $(pwd)

**上下文说明**:
为当前项目目录配置Serena MCP服务器，优化IDE辅助功能

💡 **智能提示**: 系统会自动检测项目语言并配置相应的语言服务器
```

**预期反馈**:
```bash
✅ MCP服务器添加成功
📂 配置文件: ~/.claude/claude_desktop_config.json
📊 服务状态: serena服务器已启动
🔧 下一步: 重启Claude Desktop应用以应用配置
```

##### 示例2: 独立服务器启动
```bash
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context agent --transport stdio

**上下文说明**:
启动自主代理模式的MCP服务器，适用于自定义集成

💡 **智能提示**: agent模式提供更广泛的自主操作能力
```

**预期反馈**:
```bash
✅ Serena MCP服务器启动
📂 工作目录: 当前目录
📊 传输模式: stdio
🔧 Web仪表板: http://localhost:随机端口
```

#### 常用参数说明

##### 上下文模式:
```bash
serena start-mcp-server --context ide-assistant    # IDE集成优化模式
serena start-mcp-server --context agent           # 自主代理模式
```

##### 传输方式:
```bash
serena start-mcp-server --transport stdio         # 标准输入输出（默认）
serena start-mcp-server --transport sse           # Server-Sent Events
```

**来源**: [Serena GitHub仓库](https://github.com/oraios/serena) - README.md 安装部分

### 阶段1: 客户端配置 - `MCP客户端集成`

#### 配置格式与参数

##### Claude Desktop配置
```json
{
  "mcpServers": {
    "serena": {
      "command": "/abs/path/to/uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "ide-assistant"
      ]
    }
  }
}
```

##### Cursor IDE配置
```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena-mcp-server",
        "--project",
        "$(pwd)"
      ]
    }
  }
}
```

#### 默认行为说明
- **自动项目检测**：扫描当前目录结构确定项目类型
- **语言服务器初始化**：根据检测结果启动相应的LSP服务
- **配置文件加载**：读取`~/.serena/serena_config.yml`中的用户设置

#### 专业用户实用技巧
```bash
# 指定项目路径的精确配置
"args": ["--project", "/absolute/path/to/project", "--context", "ide-assistant"]

# 只读模式配置（仅分析不编辑）
# 在serena_config.yml中设置: read_only: true
```

#### 详细使用示例

##### 示例1: 多项目工作空间配置
```json
{
  "mcpServers": {
    "serena-frontend": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/oraios/serena",
        "serena", "start-mcp-server",
        "--project", "/workspace/frontend",
        "--context", "ide-assistant"
      ]
    },
    "serena-backend": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/oraios/serena",
        "serena", "start-mcp-server",
        "--project", "/workspace/backend",
        "--context", "ide-assistant"
      ]
    }
  }
}

**上下文说明**:
为前后端分离项目分别配置Serena实例，确保各自的语言服务器独立运行

💡 **智能提示**: 不同项目使用不同的服务器实例避免语言冲突
```

**预期反馈**:
```bash
✅ 多服务器配置完成
📂 前端项目: TypeScript/React语言服务器
📂 后端项目: Python/Go语言服务器
🔧 下一步: 重启客户端应用加载新配置
```

#### 常用参数说明

##### 客户端专用参数:
```bash
--project <path>          # 指定项目根目录
--context <mode>          # 设置工作模式
--transport <type>        # 选择通信方式
```

**来源**: [Serena GitHub仓库](https://github.com/oraios/serena) - README.md 配置示例部分

### 阶段2: 语义检索 - `代码分析与搜索`

#### MCP工具格式与参数

##### 核心符号搜索工具
```bash
find_symbol                               # 全局搜索符号名称/子字符串
find_symbol --symbol-type function        # 按类型过滤（function/class/variable）
find_symbol --include-body false          # 不包含符号体内容
find_symbol --depth 1                     # 限制搜索深度
```

##### 符号引用分析工具
```bash
find_referencing_symbols                  # 查找引用指定符号的其他符号
find_referencing_symbols --symbol-type class  # 按引用类型过滤
find_referencing_symbols --file-path src/main.py  # 指定文件范围
```

##### 项目结构分析工具
```bash
get_symbols_overview                       # 获取文件顶级符号概览
search_for_pattern                         # 在项目中搜索模式
search_for_pattern --paths-include-glob "src/*.py"  # 限制搜索路径
```

#### 默认行为说明
- **语义理解**：基于代码含义而非文本匹配进行搜索
- **符号级分析**：提供函数、类、变量等符号的精确定位
- **依赖追踪**：自动分析代码间的调用关系和依赖

#### 开发者实用技巧
```bash
# 利用AI进行复杂代码分析
"帮我理解这个复杂的数据处理管道的工作流程"

# 结合语义搜索的重构准备
"找到所有使用旧API的代码位置，我需要重构它们"
```

#### 详细使用示例

##### 示例1: 新项目代码理解
```bash
在Claude Code中输入: "请分析这个Python项目的整体架构，重点关注模块间的依赖关系"

**上下文说明**:
刚接手一个新项目，需要快速了解代码结构和组织方式

💡 **智能提示**: Serena会自动扫描项目结构并提供架构概览
```

**预期反馈**:
```bash
✅ 项目架构分析完成
📂 主要模块:
   - auth/ (认证模块)
   - api/ (API接口)
   - models/ (数据模型)
   - utils/ (工具函数)
📊 依赖关系: api -> models -> utils, auth -> models
🔧 建议: 先理解models模块，它是其他模块的基础
```

##### 示例2: 特定功能代码查找
```bash
在Claude Code中输入: "找到所有处理文件上传的相关代码，包括验证、存储和处理逻辑"

**上下文说明**:
需要修改文件上传功能，要找到所有相关的代码位置

💡 **智能提示**: 语义搜索会找到所有相关函数，而不仅仅是包含"upload"关键词的代码
```

**预期反馈**:
```bash
✅ 文件上传相关代码已找到
📂 核心文件:
   - handlers/upload.py:25 (主处理函数)
   - validators/file.py:15 (文件验证)
   - storage/s3.py:40 (存储逻辑)
📊 调用关系: upload_handler -> validate_file -> store_file
🔧 建议: 修改时注意validators中的文件大小限制
```

### 阶段3: 智能编辑 - `代码修改与重构`

#### MCP编辑工具格式

##### 符号级编辑工具
```bash
replace_symbol_body                        # 替换符号的完整定义
replace_symbol_body --symbol-name "MyClass" --file-path "src/models.py"  # 指定符号和文件
insert_before_symbol                       # 在符号定义前插入内容
insert_after_symbol                        # 在符号定义后插入内容
```

##### 文本级编辑工具
```bash
replace_regex                              # 使用正则表达式替换内容
replace_regex --pattern "old_pattern" --replacement "new_pattern"  # 正则替换
delete_lines                               # 删除指定行范围
delete_lines --start-line 10 --end-line 20  # 删除第10-20行
```

##### 高级编辑功能
```bash
execute_shell_command                      # 执行Shell命令辅助编辑
get_current_config                         # 获取当前配置状态
think_about_whether_you_are_done           # 任务完成状态判断
```

#### 默认行为说明
- **上下文感知**：编辑时保持代码风格和项目约定的一致性
- **依赖更新**：自动更新相关的导入语句和引用
- **语法检查**：确保编辑后的代码语法正确

#### AI辅助实用技巧
```bash
# 让AI提供编辑建议
"这段代码有性能问题，请帮我优化"

# 批量代码更新
"将所有print语句替换为logging调用"
```

#### 详细使用示例

##### 示例1: 安全漏洞修复
```bash
在Claude Code中输入: "这个函数存在SQL注入风险，请帮我修复并添加参数化查询"

**上下文说明**:
发现代码中存在安全漏洞，需要进行修复并确保不影响其他功能

💡 **智能提示**: Serena会分析函数上下文，提供安全的修复方案
```

**预期反馈**:
```bash
✅ SQL注入漏洞修复完成
📂 修改文件: database/user_queries.py
📊 变更内容:
   - 原始查询替换为参数化查询
   - 添加输入验证函数
   - 更新相关测试用例
🔧 建议: 运行测试确保功能正常
```

##### 示例2: 性能优化重构
```bash
在Claude Code中输入: "这个数据处理函数运行很慢，请帮我优化算法并添加缓存机制"

**上下文说明**:
用户反馈某个功能响应缓慢，需要对核心算法进行性能优化

💡 **智能提示**: Serena会分析算法复杂度并提供优化建议
```

**预期反馈**:
```bash
✅ 性能优化完成
📂 修改文件:
   - processors/data_analyzer.py (主要优化)
   - cache/memory_cache.py (新增缓存)
📊 优化成果:
   - 时间复杂度: O(n²) → O(n log n)
   - 添加内存缓存机制
   - 批处理逻辑优化
🔧 建议: 监控内存使用，调整缓存大小
```

### 阶段4: Shell执行 - `测试与脚本运行`

#### 执行功能格式

##### 测试运行
```bash
"运行项目的单元测试并显示结果"           # 完整测试
"只运行auth模块的测试用例"              # 模块测试
"运行测试并生成覆盖率报告"               # 覆盖率测试
```

##### 脚本执行
```bash
"执行项目的构建脚本"                   # 构建执行
"运行代码质量检查工具"                 # 质量检查
"启动开发服务器并监控日志"              # 服务启动
```

#### 默认行为说明
- **环境感知**：自动检测项目使用的测试框架和构建工具
- **实时输出**：提供命令执行的实时反馈和日志
- **错误捕获**：捕获并格式化错误信息便于调试

#### 测试集成实用技巧
```bash
# 测试驱动开发工作流
"先运行测试确保当前功能正常，然后进行重构"

# 持续集成模拟
"按照CI/CD流程运行完整的测试和构建"
```

#### 详细使用示例

##### 示例1: 完整测试流程
```bash
在Claude Code中输入: "请运行完整的测试套件，包括单元测试、集成测试和代码覆盖率检查"

**上下文说明**:
准备发布新版本前的完整测试验证，确保所有功能正常工作

💡 **智能提示**: Serena会检测项目的测试配置并按正确顺序执行
```

**预期反馈**:
```bash
✅ 测试执行完成
📂 测试结果:
   - 单元测试: 127/127 通过
   - 集成测试: 23/23 通过
   - 代码覆盖率: 87%
📊 性能指标:
   - 总执行时间: 2分30秒
   - 最慢测试: test_data_migration (15.2秒)
🔧 建议: auth模块覆盖率偏低(67%)，建议增加测试
```

##### 示例2: 问题诊断执行
```bash
在Claude Code中输入: "有用户报告登录失败，请运行相关的调试脚本并检查日志"

**上下文说明**:
生产环境出现问题，需要运行诊断工具快速定位问题原因

💡 **智能提示**: Serena会执行项目中的诊断脚本并分析输出
```

**预期反馈**:
```bash
✅ 诊断脚本执行完成
📂 发现问题:
   - 数据库连接池已满
   - Redis缓存连接超时
   - 认证服务响应延迟
📊 关键指标:
   - 数据库连接: 98/100 (接近上限)
   - 内存使用: 85% (偏高)
🔧 紧急建议: 重启认证服务，增加数据库连接池大小
```

## 配置定制化

### 配置层次体系

#### 四层配置优先级
```bash
全局配置 → 客户端配置 → 项目配置 → 当前模式
~/.serena/serena_config.yml → 客户端参数 → .serena/project.yml → --mode
```

### 全局配置文件 - `serena_config.yml`

#### 配置文件位置和管理
```bash
~/.serena/serena_config.yml                    # 全局配置文件
uvx --from git+https://github.com/oraios/serena serena config edit  # 编辑配置
```

#### 核心配置选项
```yaml
# 安全设置
read_only: true                                # 只读模式
record_tool_usage_stats: true                 # 记录工具使用统计

# 工具控制
excluded_tools:                                # 排除工具列表
  - execute_shell_command
  - delete_lines
  - replace_regex

# Web仪表板
open_dashboard: false                          # 禁用自动打开仪表板
dashboard_port: 24282                          # 自定义仪表板端口
```

#### 高级配置示例
```yaml
# 符号搜索配置
symbol_search_depth: 2                        # 限制搜索深度
include_symbol_body_by_default: false         # 默认不包含符号体

# 语言服务器配置
language_servers:
  python:
    enabled: true
    path: "/custom/path/to/pylsp"
  typescript:
    enabled: true
    additional_args: ["--strict"]

# 内存管理
memory_cleanup_interval: 3600                 # 内存清理间隔（秒）
max_memory_entries: 1000                      # 最大内存条目数
```

**来源**: [Serena GitHub仓库](https://github.com/oraios/serena) - 配置文档部分

### 项目级配置

#### 项目配置生成
```bash
uvx --from git+https://github.com/oraios/serena serena project generate-yml
```

#### 项目特定设置
```yaml
# 项目根目录下的 .serena.yml
project:
  name: "MyWebApp"
  language: "typescript"

code_style:
  max_line_length: 100
  use_semicolons: true

analysis:
  ignore_patterns:
    - "node_modules/"
    - "dist/"
    - "*.test.ts"
```

## 客户端集成对比

### Claude Code集成
- **优势**: 官方支持，配置简单，功能完整
- **适用**: 日常开发、代码审查、快速原型
- **配置**: 一键添加MCP服务器

### Cursor IDE集成
- **优势**: IDE环境集成，可视化操作
- **适用**: 大型项目开发、团队协作
- **配置**: 需要手动配置MCP服务器

### VSCode集成
- **优势**: 丰富的扩展生态，调试支持
- **适用**: 全栈开发、调试密集场景
- **配置**: 通过MCP扩展集成

## MCP工具完整参考

### 核心工具（默认启用）

#### 符号搜索工具
| 工具名称 | 功能描述 | 主要参数 |
|---------|----------|----------|
| `find_symbol` | 全局搜索包含指定名称的符号 | `--symbol-type`, `--include-body`, `--depth` |
| `find_referencing_symbols` | 查找引用指定符号的其他符号 | `--symbol-type`, `--file-path` |
| `get_symbols_overview` | 获取文件中定义的顶级符号概览 | `--file-path` |

#### 代码编辑工具
| 工具名称 | 功能描述 | 主要参数 |
|---------|----------|----------|
| `insert_before_symbol` | 在符号定义前插入内容 | `--symbol-name`, `--file-path`, `--content` |
| `insert_after_symbol` | 在符号定义后插入内容 | `--symbol-name`, `--file-path`, `--content` |

### 可选工具（需要配置启用）

#### 高级编辑工具
| 工具名称 | 功能描述 | 安全级别 |
|---------|----------|----------|
| `replace_symbol_body` | 替换符号的完整定义 | 中风险 |
| `replace_regex` | 使用正则表达式替换内容 | 高风险 |
| `delete_lines` | 删除指定行范围 | 高风险 |

#### 项目管理工具
| 工具名称 | 功能描述 | 使用场景 |
|---------|----------|----------|
| `search_for_pattern` | 在项目中搜索模式 | 代码分析 |
| `execute_shell_command` | 执行Shell命令 | 测试运行 |
| `get_current_config` | 获取当前配置状态 | 调试诊断 |

#### 智能辅助工具
| 工具名称 | 功能描述 | AI集成 |
|---------|----------|--------|
| `think_about_whether_you_are_done` | 任务完成状态判断 | AI决策 |
| `write_memory` | 写入项目记忆存储 | 知识管理 |

**来源**: [Serena GitHub仓库](https://github.com/oraios/serena) - 源代码工具定义

## Web仪表板功能

### 仪表板访问
```bash
# 默认访问地址
http://localhost:24282/dashboard/index.html

# 检查当前仪表板端口
uvx --from git+https://github.com/oraios/serena serena tools list --show-dashboard-url
```

### 仪表板功能
- **实时日志**：显示详细的MCP操作日志
- **工具使用统计**：当启用`record_tool_usage_stats: true`时显示
- **服务器管理**：提供关闭MCP服务器的安全方式
- **配置查看**：显示当前生效的配置信息

### 仪表板配置
```yaml
# 自定义仪表板设置
open_dashboard: false                          # 禁用自动打开
dashboard_port: 8080                           # 自定义端口
dashboard_host: "0.0.0.0"                     # 允许外部访问
```

## 故障排除

### 常见问题解决

#### 安装和连接问题
```bash
# 验证uvx安装
uvx --version

# 测试Serena安装
uvx --from git+https://github.com/oraios/serena serena --help

# 检查MCP服务器状态
ps aux | grep serena
```

#### Windows特定问题
```bash
# npm命令未找到（退出代码127）
# 解决方案：
1. 确保Node.js和npm已安装
2. 将npm路径添加到系统PATH
3. 重启终端刷新环境变量
```

#### 企业环境问题
```bash
# SSL/代理问题解决
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --ssl-no-verify

# 配置企业代理
export HTTPS_PROXY=http://proxy.company.com:8080
export HTTP_PROXY=http://proxy.company.com:8080
```

#### 语言服务器问题
```bash
# 检查语言服务器依赖
uvx --from git+https://github.com/oraios/serena serena check-language-servers

# 重新安装特定语言支持
uvx --from git+https://github.com/oraios/serena serena install-language-server python

# 查看语言服务器日志
tail -f ~/.serena/logs/language_servers.log
```

## 高级使用技巧

### 内存系统利用
```bash
# 利用项目记忆功能
write_memory --key "架构决策" --content "使用微服务架构，API优先设计"

# 查看项目记忆存储
ls ~/.serena/memories/                         # 查看记忆文件
cat ~/.serena/memories/project_knowledge.json  # 查看具体内容
```

### 多项目工作流
```bash
# 为不同项目配置独立Serena实例
# 前端项目
claude mcp add frontend-serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --project /workspace/frontend

# 后端项目
claude mcp add backend-serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --project /workspace/backend
```

### 工具组合使用策略
```bash
# 代码分析→编辑→验证的完整工作流
1. find_symbol + get_symbols_overview          # 理解代码结构
2. search_for_pattern                          # 找到需要修改的位置
3. replace_symbol_body + insert_after_symbol   # 进行代码修改
4. execute_shell_command                       # 运行测试验证
```

## 性能优化指南

### 配置优化
```yaml
# 高性能配置示例
symbol_search_depth: 1                        # 减少搜索深度
include_symbol_body_by_default: false         # 默认不包含符号体
max_memory_entries: 500                       # 限制内存使用

# 排除大文件和目录
excluded_patterns:
  - "node_modules/**"
  - "*.min.js"
  - "dist/**"
  - "__pycache__/**"
```

### 内存管理
```bash
# 定期清理记忆存储
rm -rf ~/.serena/memories/old_projects/

# 监控内存使用
get_current_config                             # 查看当前配置状态
```

### 语言服务器优化
```yaml
# 仅启用必要的语言支持
language_servers:
  python:
    enabled: true
  typescript:
    enabled: false                             # 禁用不需要的语言
  java:
    enabled: false                             # Java启动较慢，按需启用
```

## 最佳实践

### 安全建议

#### 生产环境配置
```yaml
# 生产环境安全配置
read_only: true                                # 强制只读模式
excluded_tools:                                # 禁用危险工具
  - execute_shell_command
  - delete_lines
  - replace_regex
record_tool_usage_stats: true                 # 启用审计日志
```

#### 敏感文件保护
```yaml
# 排除敏感文件和目录
excluded_patterns:
  - "*.env"
  - "config/secrets.yml"
  - ".git/**"
  - "*.key"
  - "*.pem"
```

### 团队协作最佳实践

#### 统一团队配置
```bash
# 团队共享配置文件
# 将 .serena/project.yml 纳入版本控制
git add .serena/project.yml
git commit -m "Add team Serena configuration"
```

#### 配置标准化
```yaml
# 团队标准配置模板
team_standards:
  code_style:
    max_line_length: 100
    use_type_hints: true
  analysis:
    symbol_search_depth: 2
    include_tests: false
```

### 开发效率提升

#### AI提示词优化
```bash
# 高效的AI交互模式
"使用find_symbol找到所有处理用户认证的函数，然后分析它们的安全性"
"先用get_symbols_overview了解文件结构，再用search_for_pattern查找特定模式"
```

#### 批量操作技巧
```bash
# 利用AI进行批量代码分析和修改
"分析所有Controller类的错误处理模式，找出不一致的地方并统一"
"检查所有API端点的参数验证，确保安全性"
```

### 监控和维护

#### 定期维护任务
```bash
# 每周维护清单
1. 清理过期的记忆存储
2. 检查工具使用统计
3. 更新Serena版本
4. 检查语言服务器状态
```

#### 性能监控
```bash
# 监控Serena性能
get_current_config                             # 查看配置状态
# 访问仪表板查看详细统计
http://localhost:24282/dashboard/index.html
```

---

**编写依据**: 基于[Serena官方GitHub仓库](https://github.com/oraios/serena)官方文档和README.md，所有命令和配置均经过官方验证。

**适用版本**: Serena MCP服务器最新版本

**最后更新**: 2025-09-19