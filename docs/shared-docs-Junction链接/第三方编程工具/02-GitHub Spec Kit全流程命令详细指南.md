# GitHub Spec Kit全流程命令详细指南

> 基于官方GitHub仓库的规范驱动开发完整操作手册

## 官方信息源验证

### 工具基本信息
- **官方仓库**: [https://github.com/github/spec-kit](https://github.com/github/spec-kit)
- **维护者**: GitHub官方
- **项目描述**: 💫 Toolkit to help you get started with Spec-Driven Development
- **Stars数量**: 19.8k+ stars
- **License**: MIT开源协议
- **验证时间**: 2025年最新版本（当前最新：v0.0.44）

### 官方文档来源
- **核心文档**: README.md - 基本介绍和快速开始
- **方法论文档**: spec-driven.md - 规范驱动开发理论
- **官方博客**: [GitHub Blog文章](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
- **源代码**: 命令实现和配置模板位于官方仓库
- **本地实现**: 基于`.claude/commands/`目录下的实际命令配置

**来源**: [GitHub Spec Kit官方文档](https://github.com/github/spec-kit)

## 规范驱动开发架构

### 项目治理体系
- **宪法驱动**: 通过Constitution建立项目不可违背的治理原则
- **模板化流程**: 所有开发产物严格遵循既定模板
- **阶段化开发**: 强制执行五阶段开发流程，每阶段有明确检查点
- **多代理支持**: 支持Claude、Gemini、Copilot等多种AI编程助手

### 开发生命周期
```
阶段0: /constitution  → 建立项目治理原则和开发标准
阶段1: /specify      → 创建详细功能规范和业务需求
阶段2: /plan         → 设计技术方案和实施计划
阶段3: /tasks        → 分解具体开发任务和执行顺序
阶段4: /implement    → 执行实际代码实现和测试
```

### 质量保证机制
- **TDD强制执行**: 测试必须先于实现，所有测试初始失败
- **宪法合规检查**: 每个阶段验证是否符合项目治理原则
- **模板一致性**: 确保团队输出格式和质量标准统一
- **依赖关系管理**: 自动处理任务间的依赖和执行顺序

## spec-kit使用生命周期

### 阶段0: 项目治理建立 - `/constitution`

#### 命令格式与参数
```bash
/constitution [治理原则描述]                    # 基础治理原则建立
/constitution --update [更新内容]              # 更新现有治理原则
/constitution --version [版本号]               # 指定宪法版本号
/constitution --scope=[minimal|standard|comprehensive]  # 控制宪法范围
```

#### 默认行为说明
- **不带参数**: 智能更新现有治理原则，保留自定义内容，不会覆盖
- **自动版本管理**: 系统自动进行语义化版本控制
- **同步更新**: 自动更新相关模板文件，生成同步影响报告

#### AI辅助生成技巧
```bash
# 让AI根据项目类型生成
/constitution 生成电商平台项目的标准治理原则，包含性能、安全、移动端要求

# 基于现有架构生成
/constitution 基于Node.js微服务架构，生成API性能、数据安全、团队协作治理原则

# 参考行业标准生成
/constitution 参考金融行业合规要求，生成数据加密、审计日志、权限控制原则

# 针对技术能力生成
/constitution 适合小团队的简化治理原则，重点关注代码质量和基础安全
```

#### 使用时机
- **项目初始化**: 建立项目基础治理原则和开发标准
- **标准更新**: 团队开发规范需要调整时
- **移动端项目**: 添加特殊的移动应用开发要求

#### 详细使用示例

##### 示例1: 建立基础治理原则
```bash
/constitution 建立电商平台开发治理原则

**核心原则**:
- 规范优先开发: 所有功能必须先完成规范文档
- 测试驱动开发: 强制TDD流程，测试覆盖率>90%
- API响应性能: P99延迟<200ms，平均响应<50ms
- 数据安全合规: 符合PCI DSS标准，用户数据加密存储
- 移动端性能: 冷启动<3秒，数据同步<5秒
```

💡 **新手提示**: 上述示例内容完全由AI生成，你只需要告诉AI项目类型和基本要求即可
**预期反馈**:
```bash
✅ Constitution创建成功
📂 文件生成: .specify/memory/constitution.md
📋 版本信息: v1.1.0 (新增移动应用标准)
🔄 模板同步: 已更新plan-template.md的宪法检查项
⚠️  提醒: 所有后续功能开发都将按此原则执行宪法检查
```

##### 示例2: 更新移动端治理标准
```bash
/constitution 更新移动应用性能要求

**新增移动端标准**:
- 离线功能: 支持7天完全离线使用
- 电池优化: 后台消耗<5%/小时
- 平台合规: 遵循iOS App Store和Google Play指南
- 数据同步: 冲突处理采用最后写入+手动解决机制
```

**预期反馈**:
```bash
✅ Constitution更新成功
📊 版本变更: v1.1.0 → v1.2.0 (MINOR - 新增移动端标准)
🔧 同步完成:
  ✅ plan-template.md - 移动应用专项检查已更新
  ✅ spec-template.md - 移动端需求模板已对齐
  ✅ tasks-template.md - 移动端任务分类已更新
📝 建议: 现有移动项目需要重新进行宪法合规检查
```

**来源**: [.claude/commands/constitution.md](file:///E:/AI/code_2/spec-kit-test/.claude/commands/constitution.md) - 第6-69行：Constitution命令执行流程

### 阶段1: 功能需求规范 - `/specify`

#### 命令格式与参数
```bash
/specify [功能描述]                             # 标准功能规范创建
/specify --template=[web-api|mobile-app|microservice] # 使用预设模板
/specify --scope=[narrow|standard|broad]       # 控制规范范围
/specify --version=[版本号]                    # 创建或更新指定版本
/specify --branch=[分支名]                     # 指定功能分支名称
```

#### 默认行为说明
- **自动分支管理**: 自动创建功能分支（格式：001-feature-name）
- **规范模板**: 使用标准模板生成完整规范文档
- **宪法检查**: 自动验证规范是否符合项目治理原则

#### 新手友好的功能描述技巧
```bash
# 简单描述，让AI补充细节
/specify 用户登录功能

# 指定业务场景
/specify 电商网站的用户注册和登录，支持邮箱和手机号

# 包含技术要求
/specify 移动端用户认证，需要支持离线使用和生物识别

# 针对特定平台
/specify --template=mobile-app 健身追踪应用的运动数据记录功能
```

#### 使用时机
- **新功能开发**: 开始任何功能开发前必须先创建规范
- **需求明确**: 将模糊的业务需求转换为明确的技术规范
- **团队协作**: 确保所有团队成员对功能理解一致

#### 详细使用示例

##### 示例1: 用户认证系统规范
```bash
/specify 用户认证与授权管理系统

**功能概述**:
完整的用户认证体系，支持邮箱登录、手机验证、第三方登录和权限管理

**核心功能**:
- 用户注册: 邮箱/手机号注册，验证码验证，密码强度检查
- 用户登录: 多种登录方式，记住登录状态，登录失败锁定
- 权限管理: 角色权限分配，资源访问控制，权限继承
- 第三方登录: 微信、支付宝、Google OAuth集成

**技术要求**:
- JWT Token认证，30分钟过期，支持刷新机制
- 密码采用bcrypt加密，复杂度验证
- 验证码Redis存储，5分钟有效期
- 登录日志完整记录，异常行为监控

**验收标准**:
- 注册流程<60秒完成
- 登录响应时间<500ms
- 支持10000并发登录
- 密码泄露零容忍，强制加密存储
```

**预期反馈**:
```bash
✅ 功能规范创建成功
🌿 新分支: 001-user-authentication (已切换)
📂 规范文件: specs/001-user-authentication/spec.md
📋 内容包含:
  - 用户故事和业务场景
  - 功能需求和非功能需求
  - API接口设计概要
  - 验收标准和测试场景
🔄 下一步: 使用 /plan 命令创建技术实施计划
```

##### 示例2: 移动端离线数据同步
```bash
/specify 移动应用离线数据同步功能

**业务场景**:
用户在网络不稳定或离线环境下，仍能正常使用核心功能，数据自动同步

**功能详述**:
- 离线存储: SQLite本地数据库，支持7天离线使用
- 数据同步: 增量同步，冲突检测，智能合并策略
- 缓存策略: 关键数据预加载，图片懒加载，存储空间管理
- 网络监控: 实时网络状态检测，自动重连机制

**性能约束**:
- 首次同步时间<30秒
- 增量同步延迟<3秒
- 本地存储占用<200MB
- 同步冲突解决成功率>99%

**平台适配**:
- iOS 14+ 和 Android 8+ 兼容
- React Native统一代码库
- 原生SQLite性能优化
- 平台特有网络API集成
```

**预期反馈**:
```bash
✅ 移动端功能规范创建成功
🌿 新分支: 002-offline-sync (已切换)
📂 规范文件: specs/002-offline-sync/spec.md
🔧 宪法检查: 通过移动应用专项检查
  ✅ 离线优先设计 - 支持7天离线使用
  ✅ 性能标准 - 同步时间<30秒
  ✅ 平台合规 - 兼容性要求明确
📝 特殊注意: 移动端项目需要额外的原生模块集成
🔄 下一步: 使用 /plan 命令设计离线同步架构
```

**来源**: [.claude/commands/specify.md](file:///E:/AI/code_2/spec-kit-test/.claude/commands/specify.md) - 第5-14行：Specify命令执行流程





### 阶段二：需求规范定义

#### 基础命令结构
```bash
/specify "需求描述内容"
```

#### 高级参数选项
```bash
# 使用预设模板
/specify --template=web-api "用户认证API系统"
/specify --template=mobile-app "社交网络应用"
/specify --template=microservice "订单处理服务"

# 控制规范范围
/specify --scope=narrow "用户登录功能"        # 单一功能模块
/specify --scope=standard "用户管理系统"      # 完整功能模块
/specify --scope=broad "企业ERP系统"          # 跨模块系统

# 版本管理
/specify --version=v1.1 "更新需求描述"
```

#### 内容填写框架

##### 推荐结构模板
```bash
/specify "
项目名称：[简洁明确的项目标识]

**业务背景**：
- 解决的核心问题
- 目标用户群体定义
- 预期业务价值

**核心功能**：
- 功能模块1：具体描述 + 关键技术点
- 功能模块2：具体描述 + 关键技术点
- 功能模块3：具体描述 + 关键技术点

**性能要求**：
- API响应时间：具体数值指标
- 并发处理能力：用户数量/QPS
- 系统可用性：百分比目标

**技术约束**：
- 必选技术栈组件
- 系统兼容性要求
- 安全合规标准

**验收标准**：
- 可量化的成功指标
- 用户体验质量目标
- 系统性能基准
"
```

##### 实际填写示例

**电商订单系统**:
```bash
/specify "
电商平台订单管理系统重构

**业务背景**：
- 替换遗留订单处理系统，提升运营效率
- 服务B2C电商平台，处理日均50000+订单
- 减少客服工作量60%，提升用户满意度

**核心功能**：
- 订单创建：多商品组合、优惠券计算、实时库存验证、支付集成
- 状态跟踪：订单生命周期管理、物流信息同步、异常自动处理
- 退款处理：自动化退款流程、部分退款支持、财务对账集成
- 数据分析：订单趋势分析、用户行为洞察、业务报表生成

**性能要求**：
- API响应时间：平均<100ms，P99<500ms
- 并发处理：支持10000订单/分钟高峰
- 系统可用性：99.95%在线率
- 数据一致性：订单-库存-支付强一致

**技术约束**：
- 微服务架构，Spring Cloud Netflix技术栈
- 数据存储：MySQL主从复制 + Redis分布式缓存
- 消息处理：RabbitMQ异步解耦 + 死信队列
- 容器部署：Docker + Kubernetes + Istio服务网格

**验收标准**：
- 订单处理延迟降低60%（从15秒到6秒）
- 客服工单减少40%（月均从2000降到1200）
- 系统故障恢复时间<30分钟
- 订单数据准确率99.99%
"
```

**移动健身应用**:
```bash
/specify "
个人健身数据追踪移动应用

**业务背景**：
- 面向健身爱好者的专业运动数据平台
- 差异化定位：专注力量训练数据深度分析
- 竞品分析：Keep通用化 vs 本产品专业化

**核心功能**：
- 运动记录：手动输入、智能识别、穿戴设备同步、离线记录
- 数据分析：进度可视化、趋势预测、同期对比、目标设定
- 社交互动：好友系统、运动打卡、成就排行、挑战活动
- 智能推荐：基于历史数据的个性化训练计划推荐

**性能要求**：
- 应用冷启动：iOS/Android均<3秒
- 数据同步延迟：云端同步<5秒完成
- 离线功能：支持7天完全离线使用
- 电池消耗：后台运行<5%电量/小时

**技术约束**：
- 跨平台开发：React Native统一代码库
- 后端架构：Node.js + Express + MongoDB
- 实时通信：WebSocket保持连接
- 数据策略：本地SQLite + 云端MongoDB双重备份

**验收标准**：
- 30天用户留存率>40%
- 日活跃用户目标50000
- 应用商店评分>4.5星
- 数据同步成功率99.9%
"
```

**来源**: [GitHub Spec Kit Command Reference](https://github.com/github/spec-kit/blob/main/docs/commands.md)

### 阶段2: 技术方案设计 - `/plan`

#### 命令格式与参数
```bash
/plan [技术实施细节]                            # 基础技术方案生成
/plan --stack [技术栈组合]                     # 指定技术栈架构
/plan --constraints [约束条件列表]              # 添加技术和业务约束
/plan --compare=[方案A vs 方案B]               # 多方案对比分析
/plan --architecture=[monolith|microservice|serverless] # 架构模式选择
/plan --platform=[web|mobile|desktop|cloud]   # 目标平台指定
```

#### 默认行为说明
- **智能技术选型**: 基于spec.md自动推荐合适的技术栈
- **自动架构设计**: 生成系统架构图和组件设计
- **宪法合规检查**: 验证技术方案是否符合治理原则

#### 技术选型建议（适合新手）
```bash
# 让AI推荐技术栈
/plan 基于功能需求推荐最适合的技术栈

# 指定熟悉的技术
/plan --stack "我熟悉JavaScript,想用Node.js和React"

# 考虑团队技能
/plan --constraints "团队主要熟悉Python和Vue.js,希望避免过于复杂的架构"

# 预算和资源约束
/plan --constraints "小型项目,预算有限,希望使用免费开源技术"
```

#### 使用时机
- **功能规范完成后**: 基于spec.md创建技术实施方案
- **架构设计阶段**: 确定技术栈、系统架构和实施策略
- **宪法合规检查**: 验证技术方案是否符合项目治理原则

#### 详细使用示例

##### 示例1: 用户认证系统技术方案
```bash
/plan 使用JWT+Redis的高性能认证架构

**技术栈选择**:
- 后端框架: Node.js + Express + TypeScript
- 数据库: PostgreSQL主库 + Redis缓存
- 认证机制: JWT + RefreshToken双令牌机制
- 加密算法: bcrypt密码哈希 + AES-256数据加密
- 第三方集成: OAuth 2.0 + 微信/支付宝SDK

**系统架构**:
- 微服务分离: Auth Service独立部署
- 负载均衡: Nginx反向代理 + SSL终止
- 缓存策略: Redis存储session + token黑名单
- 监控告警: 登录异常实时监控 + 风控策略

**性能优化**:
- 数据库连接池: 最大50连接，超时30秒
- JWT过期策略: 访问令牌15分钟，刷新令牌7天
- 缓存命中率: 登录验证缓存命中率>95%
- 并发处理: 支持10000/QPS登录请求
```

**预期反馈**:
```bash
✅ 技术方案生成成功
📊 宪法合规检查: ✅ 通过
  ✅ 规范优先开发 - 基于完整spec.md生成
  ✅ 测试驱动开发 - 包含完整测试策略
  ✅ 代理无关开发 - 支持多AI工具协作
📂 生成文件:
  └── specs/001-user-authentication/
      ├── plan.md              # 技术实施计划
      ├── research.md          # 技术调研结果
      ├── data-model.md        # 数据模型设计
      ├── quickstart.md        # 快速开始指南
      └── contracts/           # API契约定义
          ├── auth-api.yaml    # 认证API规范
          └── user-api.yaml    # 用户管理API规范
🔧 下一步: 使用 /tasks 命令生成具体开发任务
```

##### 示例2: 移动端离线同步架构设计
```bash
/plan React Native + SQLite离线优先架构

**移动端技术栈**:
- 跨平台框架: React Native 0.73+
- 本地存储: SQLite + Realm数据库
- 状态管理: Redux Toolkit + RTK Query
- 网络层: Axios + 请求重试机制
- 原生模块: 网络监控 + 后台同步

**同步架构设计**:
- 数据版本控制: 时间戳 + 版本号双重标识
- 冲突解决策略: 最后写入优先 + 手动冲突解决
- 增量同步: 仅同步变更数据，减少流量消耗
- 离线队列: 本地操作队列，网络恢复后批量同步

**性能约束实现**:
- 冷启动优化: 预加载关键数据，启动时间<3秒
- 数据压缩: gzip压缩API响应，减少50%流量
- 存储管理: 自动清理过期缓存，控制应用大小<200MB
- 电池优化: 智能同步频率，后台消耗<5%/小时
```

**预期反馈**:
```bash
✅ 移动端技术方案生成成功
📊 移动应用专项检查: ✅ 通过
  ✅ 架构要求 - 移动端+API分离设计
  ✅ 性能标准 - 冷启动<3秒，同步<5秒
  ✅ 平台合规 - React Native跨平台兼容
📂 生成文件:
  └── specs/002-offline-sync/
      ├── plan.md              # 移动端架构方案
      ├── research.md          # 离线同步技术调研
      ├── data-model.md        # 本地数据模型
      ├── quickstart.md        # 集成测试指南
      └── contracts/
          ├── sync-api.yaml    # 数据同步API规范
          └── offline-api.yaml # 离线功能API规范
⚠️  特殊提醒: 移动端项目需要额外配置原生模块依赖
🔧 下一步: 使用 /tasks 命令分解移动端开发任务
```

#### 常用参数说明

##### 技术栈组合示例
```bash
# 现代Web全栈应用
/plan --stack "React,TypeScript,Node.js,Express,PostgreSQL,Redis,Docker"

# 企业级微服务架构
/plan --stack "Spring Boot,MySQL,RabbitMQ,Redis,Docker,Kubernetes,Jenkins"

# 移动应用后端系统
/plan --stack "Node.js,Express,MongoDB,Redis,JWT,Socket.io,AWS"

# 大数据分析平台
/plan --stack "Python,Django,PostgreSQL,Elasticsearch,Kafka,Docker,Airflow"

# 高性能实时系统
/plan --stack "Go,Gin,Redis,PostgreSQL,gRPC,Kubernetes,Prometheus"
```

##### 约束条件示例
```bash
# 性能和规模约束
/plan --constraints "支持100万用户,API响应<200ms,99.9%可用性"

# 技术和合规约束
/plan --constraints "必须使用开源技术,符合GDPR,PCI DSS合规"

# 团队和资源约束
/plan --constraints "团队5人,开发周期6个月,预算100万"

# 集成和兼容约束
/plan --constraints "集成现有ERP,支持IE11,多租户架构"
```

##### 架构模式选择
- **monolith**: 单体应用架构，适合小型项目
- **microservice**: 微服务架构，适合大型复杂系统
- **serverless**: 无服务器架构，适合事件驱动应用

**来源**: [.claude/commands/plan.md](file:///E:/AI/code_2/spec-kit-test/.claude/commands/plan.md) - 第6-36行：Plan命令执行流程

### 阶段3: 开发任务分解 - `/tasks`

#### 命令格式与参数
```bash
/tasks [任务生成上下文]                         # 标准粒度任务分解
/tasks --granularity=[high-level|standard|detailed] # 任务分解粒度控制
/tasks --output=[github-issues|jira|markdown] # 输出格式选择
/tasks --filter=[setup|tests|core|integration|polish] # 按类别过滤任务
/tasks --parallel                              # 标记可并行执行任务
/tasks --estimate                              # 添加时间估算
```

#### 默认行为说明
- **标准模式默认包含**:
  - `--output=markdown` (生成本地tasks.md文件)
  - `--granularity=standard` (20-30个任务，每任务1-3天)
  - `--parallel` (自动标记可并行任务[P])
- **不包含**: 时间估算(需要显式添加`--estimate`)
- **上下文自动识别**: 自动读取plan.md、data-model.md、contracts/等文件

#### 个人vs团队开发选择
```bash
# 个人开发 (推荐)
/tasks                                         # 默认markdown格式，本地管理

# 团队开发
/tasks --output=github-issues                  # 生成GitHub Issues模板
/tasks --output=jira                           # 生成Jira兼容格式
```

#### 使用时机
- **技术方案确定后**: 基于plan.md等设计文档生成具体任务
- **开发前准备**: 将技术方案分解为可执行的开发任务
- **团队分工**: 按任务依赖关系安排并行和串行工作

#### 详细使用示例

##### 示例1: 用户认证系统任务分解
```bash
/tasks 生成用户认证模块完整开发任务列表

**上下文说明**:
基于已完成的技术方案，包含JWT认证、Redis缓存、PostgreSQL存储的完整认证体系，需要分解为具体的开发和测试任务。

💡 **智能提示**: AI会自动识别上下文，包括技术栈、架构设计等。人工描述主要用于强调特殊要求或补充信息。
```

**预期反馈**:
```bash
✅ 开发任务生成成功
📂 任务文件: specs/001-user-authentication/tasks.md
📊 任务概览:
  - 总任务数: 23个
  - Setup任务: 3个 (环境配置、依赖安装)
  - Test任务: 8个 [P] (契约测试、集成测试)
  - Core任务: 7个 (核心功能实现)
  - Integration任务: 3个 (数据库、缓存集成)
  - Polish任务: 2个 [P] (性能优化、文档)

📋 任务分类详情:
【Setup阶段】
T001: 项目环境初始化和依赖安装
T002: PostgreSQL数据库配置和迁移脚本
T003: Redis缓存配置和连接测试

【Tests阶段 - 可并行执行[P]】
T004: [P] 用户注册API契约测试 (auth-api.yaml验证)
T005: [P] 登录认证API契约测试 (JWT token验证)
T006: [P] 权限验证API契约测试 (角色权限检查)
T007: [P] 第三方登录集成测试 (OAuth流程)
T008: [P] 密码重置流程集成测试
T009: [P] 用户注册完整流程集成测试
T010: [P] 登录状态维护集成测试
T011: [P] 权限控制完整流程测试

【Core阶段】
T012: User实体模型实现 (data-model.md)
T013: 用户注册服务实现 (密码加密、验证码)
T014: 登录认证服务实现 (JWT生成、验证)
T015: 权限管理服务实现 (角色权限分配)
T016: 第三方登录服务实现 (OAuth集成)
T017: 用户管理API端点实现
T018: 认证中间件实现 (token验证、权限检查)

【Integration阶段】
T019: PostgreSQL数据库连接和ORM配置
T020: Redis缓存服务集成和session管理
T021: 邮件服务集成 (验证码发送)

【Polish阶段 - 可并行执行[P]】
T022: [P] API性能优化和缓存策略调优
T023: [P] API文档生成和使用说明更新

🔄 执行建议:
- Setup任务按顺序执行 (T001→T002→T003)
- Tests任务可以并行开发 (T004-T011同时进行)
- Core任务按依赖顺序 (T012→T013-T016→T017-T018)
- Integration任务可以并行集成 (T019-T021)
- Polish任务最后并行完成 (T022-T023)

🔧 下一步: 使用 /implement 命令开始执行任务
```

##### 示例2: 移动端同步功能任务分解
```bash
/tasks 分解React Native离线同步功能开发任务

**特殊要求**:
移动端项目需要考虑iOS和Android平台差异，原生模块集成，以及离线存储的复杂性。
```

**预期反馈**:
```bash
✅ 移动端任务生成成功
📂 任务文件: specs/002-offline-sync/tasks.md
📊 任务概览:
  - 总任务数: 28个
  - Setup任务: 5个 (跨平台环境配置)
  - Test任务: 12个 [P] (移动端特殊测试)
  - Core任务: 8个 (核心同步逻辑)
  - Integration任务: 3个 (原生模块集成)

📋 移动端特殊任务:
【Setup阶段】
T001: React Native项目初始化和依赖配置
T002: SQLite数据库模块安装和配置
T003: Redux Toolkit状态管理配置
T004: iOS原生模块配置 (网络监控、后台同步)
T005: Android原生模块配置 (网络监控、后台同步)

【Tests阶段 - 移动端测试[P]】
T006: [P] SQLite本地存储契约测试
T007: [P] 数据同步API契约测试
T008: [P] 网络状态监控集成测试
T009: [P] 离线队列机制测试
T010: [P] 冲突解决策略测试
T011: [P] iOS平台集成测试
T012: [P] Android平台集成测试
T013: [P] 跨平台数据一致性测试
T014: [P] 后台同步性能测试
T015: [P] 电池消耗测试
T016: [P] 离线7天使用场景测试
T017: [P] 数据压缩和传输优化测试

【Core阶段】
T018: 本地数据模型实现 (SQLite schema)
T019: 数据同步管理器实现 (SyncManager)
T020: 网络状态监控服务 (NetworkService)
T021: 离线操作队列实现 (OfflineQueue)
T022: 冲突检测和解决逻辑 (ConflictResolver)
T023: 数据压缩和序列化服务
T024: Redux状态管理集成
T025: 同步状态UI组件实现

【Integration阶段】
T026: iOS后台同步原生模块集成
T027: Android后台同步原生模块集成
T028: 跨平台网络库统一封装

⚠️  移动端特殊注意:
- T004/T005需要原生开发经验
- T011/T012需要真机测试环境
- T015需要长时间电池测试
- 建议按平台分组并行开发

🔧 下一步: 使用 /implement 命令执行移动端开发任务
```

#### 常用参数说明

##### 分解粒度控制
```bash
# 高层级分解 (项目规划、管理层汇报)
/tasks --granularity=high-level            # 3-5个主要开发阶段，每阶段1-2周

# 标准分解 (团队协作、敏捷开发) - 默认
/tasks --granularity=standard              # 20-30个具体功能任务，每任务1-3天

# 详细分解 (技术实现、代码开发)
/tasks --granularity=detailed              # 30-50个细化任务，每任务0.5-2天
```

##### 输出格式选择
```bash
# GitHub Issues格式 (团队协作)
/tasks --output=github-issues              # 生成可直接导入GitHub的Issue模板

# Jira格式 (企业项目管理)
/tasks --output=jira                       # 生成Jira兼容的任务格式

# Markdown格式 (个人开发，默认)
/tasks --output=markdown                   # 生成本地tasks.md任务列表
```

##### 任务过滤和分类
```bash
# 按类别过滤
/tasks --filter=setup                      # 仅生成环境配置任务
/tasks --filter=tests                      # 仅生成测试相关任务
/tasks --filter=core                       # 仅生成核心功能任务
/tasks --filter=integration                # 仅生成集成任务
/tasks --filter=polish                     # 仅生成优化完善任务

# 并行任务标记 (默认启用)
/tasks --parallel                          # 强制启用并行标记（通常不需要显式指定）

# 时间估算
/tasks --estimate                          # 为每个任务添加时间估算
```

##### 任务分类系统说明
- **Setup**: 环境配置、依赖安装、基础设施搭建
- **Tests [P]**: 契约测试、集成测试（可并行执行）
- **Core**: 核心业务逻辑实现、数据模型创建
- **Integration**: 外部系统集成、中间件配置
- **Polish [P]**: 性能优化、文档完善（可并行执行）

**来源**: [.claude/commands/tasks.md](file:///E:/AI/code_2/spec-kit-test/.claude/commands/tasks.md) - 第6-58行：Tasks命令执行流程

### 阶段4: 代码实现执行 - `/implement`

#### 命令格式与参数
```bash
/implement [实现执行上下文]                     # 执行所有任务
/implement --task-filter=[backend|frontend|mobile] # 仅执行特定类型任务
/implement --category=[setup|tests|core|integration|polish] # 按阶段执行
/implement --parallel                           # 并行执行可并行任务
/implement --dry-run                            # 预览执行计划不实际执行
/implement --continue-on-error                  # 遇到错误继续执行其他任务
/implement --rollback-on-failure                # 失败时自动回滚已完成任务
/implement --progress-report                    # 显示详细执行进度
```

#### 默认行为说明
- **智能任务排序**: 根据依赖关系自动安排执行顺序
- **TDD强制执行**: 测试任务优先于实现任务
- **自动并行处理**: 自动识别并并行执行独立任务
- **错误自动重试**: 失败任务提供修复建议并支持重试

#### 新手安全执行建议
```bash
# 先预览执行计划（推荐）
/implement --dry-run                            # 查看将要执行的任务，不实际执行

# 分阶段执行（安全）
/implement --category=setup                     # 先执行环境配置
/implement --category=tests                     # 再执行测试编写
/implement --category=core                      # 然后执行核心功能

# 保守执行模式
/implement --continue-on-error --progress-report # 遇到错误不停止，显示详细进度
```

#### 使用时机
- **任务列表完成后**: 基于tasks.md按顺序执行所有开发任务
- **TDD执行阶段**: 先执行测试任务，再执行实现任务
- **完整功能交付**: 从环境配置到代码实现的全流程自动化

#### 详细使用示例

##### 示例1: 用户认证系统完整实现
```bash
/implement 执行用户认证模块所有开发任务

**执行策略**:
按照TDD原则，优先执行测试任务，然后按依赖关系执行实现任务，确保每个阶段完成后进行验证。
```

**预期反馈**:
```bash
✅ 开始执行实现计划
📂 任务来源: specs/001-user-authentication/tasks.md
📊 执行计划: 23个任务，预计45分钟

🔄 【Setup阶段执行中】
⏳ T001: 项目环境初始化和依赖安装...
✅ T001: 完成 (2分钟) - 依赖安装成功，环境配置完毕
⏳ T002: PostgreSQL数据库配置和迁移脚本...
✅ T002: 完成 (3分钟) - 数据库连接成功，表结构创建完毕
⏳ T003: Redis缓存配置和连接测试...
✅ T003: 完成 (1分钟) - Redis连接正常，缓存测试通过

🔄 【Tests阶段并行执行中】
⏳ 并行执行: T004-T011 (8个测试任务)
✅ T004: [P] 用户注册API契约测试 - 通过 (2分钟)
✅ T005: [P] 登录认证API契约测试 - 通过 (2分钟)
✅ T006: [P] 权限验证API契约测试 - 通过 (2分钟)
✅ T007: [P] 第三方登录集成测试 - 通过 (3分钟)
❌ T008: [P] 密码重置流程集成测试 - 失败
    错误: 邮件服务配置缺失，无法发送验证码
⏳ 修复中: 配置SMTP邮件服务...
✅ T008: [P] 重新执行 - 通过 (1分钟)
✅ T009-T011: [P] 其他集成测试 - 全部通过 (4分钟)

🔄 【Core阶段顺序执行中】
⏳ T012: User实体模型实现...
✅ T012: 完成 (4分钟) - User模型创建，字段验证添加
⏳ T013: 用户注册服务实现...
✅ T013: 完成 (6分钟) - 注册逻辑完成，密码加密正常
⏳ T014: 登录认证服务实现...
✅ T014: 完成 (5分钟) - JWT生成和验证功能完成
⏳ T015-T018: 其他核心服务...
✅ T015-T018: 全部完成 (18分钟) - 所有核心功能实现完毕

🔄 【Integration阶段并行执行中】
✅ T019-T021: 完成 (8分钟) - 数据库、缓存、邮件服务集成完毕

🔄 【Polish阶段并行执行中】
✅ T022: [P] API性能优化 - 完成 (3分钟)
✅ T023: [P] API文档更新 - 完成 (2分钟)

📊 执行完成报告:
✅ 总任务数: 23个
✅ 成功完成: 23个
❌ 初始失败: 1个 (已修复)
⏱️  总执行时间: 43分钟
📈 测试通过率: 100%

📂 生成文件:
├── src/
│   ├── models/User.js               # 用户实体模型
│   ├── services/AuthService.js     # 认证服务
│   ├── services/UserService.js     # 用户管理服务
│   ├── middleware/auth.js           # 认证中间件
│   └── routes/auth.js              # 认证路由
├── tests/
│   ├── contracts/auth.test.js       # 契约测试
│   ├── integration/auth.test.js     # 集成测试
│   └── unit/services.test.js        # 单元测试
├── config/
│   ├── database.js                  # 数据库配置
│   ├── redis.js                     # 缓存配置
│   └── mail.js                      # 邮件配置
└── docs/
    └── api/auth.md                  # API文档

🎯 验证结果:
✅ 所有契约测试通过
✅ 集成测试覆盖率100%
✅ API响应时间平均45ms
✅ 10000并发登录测试通过
✅ 宪法合规检查通过

🔄 后续建议:
1. 运行完整的端到端测试
2. 进行性能压力测试
3. 部署到测试环境验证
```

##### 示例2: 移动端同步功能实现
```bash
/implement 执行React Native离线同步功能开发

**特殊配置**:
移动端项目需要配置iOS和Android原生模块，执行过程中需要真机测试环境。
```

**预期反馈**:
```bash
✅ 移动端实现开始执行
📂 任务来源: specs/002-offline-sync/tasks.md
📊 执行计划: 28个任务，预计65分钟

🔄 【Setup阶段执行中】
✅ T001: React Native项目初始化 - 完成 (5分钟)
✅ T002: SQLite数据库模块配置 - 完成 (3分钟)
✅ T003: Redux Toolkit状态管理配置 - 完成 (4分钟)
⚠️  T004: iOS原生模块配置...
    提醒: 需要Xcode环境，正在配置网络监控模块
✅ T004: iOS原生模块配置 - 完成 (8分钟)
⚠️  T005: Android原生模块配置...
    提醒: 需要Android Studio环境，正在配置后台同步
✅ T005: Android原生模块配置 - 完成 (6分钟)

🔄 【Tests阶段并行执行中】
⏳ 并行执行: T006-T017 (12个移动端测试)
✅ T006-T010: [P] 基础功能测试 - 全部通过 (15分钟)
⚠️  T011: [P] iOS平台集成测试 - 需要真机测试
    正在连接iOS模拟器...
✅ T011: [P] iOS平台测试 - 通过 (8分钟)
⚠️  T012: [P] Android平台集成测试 - 需要真机测试
    正在连接Android模拟器...
✅ T012: [P] Android平台测试 - 通过 (7分钟)
✅ T013-T017: [P] 其他专项测试 - 全部通过 (20分钟)

🔄 【Core阶段顺序执行中】
✅ T018-T025: 核心功能实现 - 全部完成 (35分钟)
    - SQLite数据模型创建完毕
    - 同步管理器实现完成
    - 离线队列机制正常工作
    - 冲突解决逻辑测试通过
    - Redux状态管理集成完毕

🔄 【Integration阶段执行中】
✅ T026: iOS后台同步集成 - 完成 (8分钟)
✅ T027: Android后台同步集成 - 完成 (8分钟)
✅ T028: 跨平台网络库封装 - 完成 (5分钟)

📊 移动端执行完成报告:
✅ 总任务数: 28个
✅ 成功完成: 28个
⏱️  总执行时间: 63分钟
📱 平台覆盖: iOS + Android
🔋 电池测试: 后台消耗4.2%/小时 (达标<5%)
💾 存储占用: 180MB (达标<200MB)

📂 移动端生成文件:
├── src/
│   ├── models/LocalDB.js            # SQLite数据模型
│   ├── services/SyncManager.js      # 同步管理器
│   ├── services/NetworkService.js   # 网络监控服务
│   ├── utils/OfflineQueue.js        # 离线队列
│   ├── utils/ConflictResolver.js    # 冲突解决器
│   └── components/SyncStatus.js     # 同步状态组件
├── ios/
│   └── NetworkMonitor.swift         # iOS网络监控模块
├── android/
│   └── NetworkMonitor.java          # Android网络监控模块
└── tests/
    ├── __tests__/sync.test.js        # 同步功能测试
    ├── e2e/ios.test.js              # iOS端到端测试
    └── e2e/android.test.js          # Android端到端测试

🎯 移动端验证结果:
✅ 离线7天使用测试通过
✅ 数据同步延迟<3秒
✅ 冲突解决成功率99.8%
✅ 跨平台数据一致性验证通过
✅ 移动应用宪法检查通过

📱 下一步建议:
1. 在真机环境进行完整测试
2. 提交App Store和Google Play审核
3. 配置生产环境同步服务器
```

#### 常用参数说明

##### 任务过滤选项
```bash
# 按技术栈过滤
/implement --task-filter=backend            # 仅执行后端相关任务
/implement --task-filter=frontend           # 仅执行前端相关任务
/implement --task-filter=mobile             # 仅执行移动端相关任务
/implement --task-filter=database           # 仅执行数据库相关任务

# 按开发阶段过滤
/implement --category=setup                 # 仅执行环境配置任务
/implement --category=tests                 # 仅执行测试相关任务
/implement --category=core                  # 仅执行核心功能开发
/implement --category=integration           # 仅执行集成任务
/implement --category=polish                # 仅执行完善和优化任务
```

##### 执行控制选项
```bash
# 执行模式控制
/implement --dry-run                        # 预览执行计划，不实际执行
/implement --parallel                       # 并行执行可并行任务[P]
/implement --sequential                     # 强制顺序执行所有任务

# 错误处理策略
/implement --continue-on-error              # 遇到错误继续执行其他任务
/implement --rollback-on-failure            # 失败时自动回滚已完成任务
/implement --retry-failed=[次数]            # 失败任务自动重试次数

# 监控和报告
/implement --progress-report                # 显示详细执行进度
/implement --verbose                        # 显示详细执行日志
/implement --silent                         # 静默执行，仅显示结果
```

##### 质量控制选项
```bash
# 测试和验证
/implement --skip-tests                     # 跳过测试执行（不推荐）
/implement --coverage-threshold=90          # 设置测试覆盖率阈值
/implement --lint-check                     # 强制代码格式检查
/implement --typecheck                      # 强制类型检查

# 性能监控
/implement --performance-benchmark          # 执行性能基准测试
/implement --memory-limit=512MB             # 设置内存使用限制
/implement --timeout=3600                   # 设置总执行超时时间（秒）
```

#### 实现执行特性

##### 智能任务执行
- **任务顺序**: 根据依赖关系自动排序任务执行顺序
- **并行执行**: 不同文件的任务标记[P]可并行执行
- **TDD优先**: 测试任务优先于对应的实现任务执行
- **依赖检查**: 自动验证前置任务完成状态
- **错误处理**: 失败任务自动重试，提供修复建议

##### 执行监控和进度跟踪
- **实时进度**: 显示当前执行任务和预计完成时间
- **任务状态**: 标记任务为 完成(✅) / 进行中(⏳) / 失败(❌) / 跳过(⚠️)
- **性能指标**: 监控执行时间、测试覆盖率、性能基准
- **质量验证**: 自动运行lint、typecheck、测试验证

**来源**: [.claude/commands/implement.md](file:///E:/AI/code_2/spec-kit-test/.claude/commands/implement.md) - 第6-52行：Implement命令执行流程

## 完整项目示例

### 在线教育平台实施流程

#### 第1步：项目环境准备
```bash
# 创建项目目录
mkdir online-education-platform
cd online-education-platform

# 初始化Spec Kit项目
uvx --from git+https://github.com/github/spec-kit.git specify init education-platform
```

#### 第2步：业务需求规范
```bash
/specify "
在线教育平台核心教学模块

**业务背景**：
- 为K12教育机构提供完整在线教学解决方案
- 服务教师、学生、家长三方用户群体
- 核心优势：强互动性教学 + 精准学习数据分析

**核心功能**：
- 课程管理：课程创建发布、视频内容上传、教学资料共享、作业任务布置
- 直播教学：实时音视频互动、电子白板协作、学生举手发言、课程录制回放
- 学习跟踪：个人学习进度监控、学习成绩统计分析、学习报告生成、学习预警提醒
- 社区互动：课程内容讨论、师生答疑解惑、同学学习交流、教师教学反馈

**性能要求**：
- 同时在线：支持1000人并发直播上课
- 视频传输：音视频延迟控制在200ms以内
- 系统稳定：99.9%服务可用性保证
- 存储容量：支持100TB海量课程视频存储

**技术约束**：
- 多端支持：iOS/Android移动APP + PC Web浏览器
- 支付集成：微信支付、支付宝、银行卡支付
- 数据合规：符合教育行业数据隐私保护法规
- 内容分发：CDN全球加速降低视频加载延迟

**验收标准**：
- 用户注册到首次上课全流程<5分钟
- 教师发布课程操作流程<3个步骤
- 学生课程完成率平均>80%
- 1000并发用户压力测试稳定运行
"
```

#### 第3步：技术方案设计
```bash
/plan --stack "Vue.js,TypeScript,Node.js,Express,MySQL,Redis,WebRTC,Docker,AWS" --constraints="支持10000注册用户,视频存储100TB,多设备数据同步,7x24高可用服务"
```

#### 第4步：开发任务分解
```bash
/tasks --granularity=detailed --output=github-issues
```

**来源**: [GitHub Spec Kit Complete Workflow](https://github.com/github/spec-kit/blob/main/examples/)

## 高级功能应用

### 版本控制和迭代

#### 规范版本管理
```bash
# 创建规范版本
/specify --version=v1.0 "初始需求规范"

# 版本更新迭代
/specify --version=v1.1 "需求优化和功能增强"

# 版本差异对比
specify diff v1.0 v1.1
```

#### 方案评估对比
```bash
# 多方案技术对比
/plan --compare="微服务架构 vs 单体应用架构"

# 成本效益分析
/plan --constraints="预算50万 vs 预算100万对比"
```

### GitHub集成配置

#### 自动化资源创建
```bash
# GitHub仓库集成设置
specify github-setup --repo education-platform

# 自动创建GitHub资源
specify integration --platform=github --auto-create
```

#### 生成GitHub配置内容
- **Issues创建**: 基于任务分解自动生成详细Issues
- **项目看板**: 设置待办/进行中/已完成状态管理
- **CI/CD配置**: GitHub Actions自动化工作流
- **模板文件**: Issue和PR标准化模板

**来源**: [GitHub Spec Kit Integration Guide](https://github.com/github/spec-kit/blob/main/docs/github-integration.md)

## 故障排除指南

### Spec-kit版本更新指导

#### 版本状态检查
```bash
# 检查当前系统配置和工具版本
uvx --from git+https://github.com/github/spec-kit.git specify check

# 验证项目配置状态
ls -la .specify/                    # 检查配置目录结构
cat .specify/memory/constitution_update_checklist.md  # 查看版本信息
```

#### 官方更新方法
```bash
# 方式1：在现有项目目录更新
uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai claude

# 方式2：强制获取最新版本（清理缓存）
uvx --from git+https://github.com/github/spec-kit.git@main specify init --here --ai claude

# 方式3：检查更新但不执行（预览模式）
uvx --from git+https://github.com/github/spec-kit.git specify check --preview
```

#### 更新前备份操作
```bash
# 备份现有配置（推荐）
cp -r .specify .specify.backup.$(date +%Y%m%d)

# 备份项目文档
cp -r spec spec.backup.$(date +%Y%m%d)

# 验证备份完整性
ls -la *.backup.*
```

#### 更新后验证步骤
```bash
# 检查配置文件结构
find .specify -name "*.md" -exec echo "=== {} ===" \; -exec head -5 {} \;

# 验证核心命令可用性
uvx --from git+https://github.com/github/spec-kit.git specify --help

# 测试项目特定功能
/specify --version
/plan --help
/tasks --help
```

#### 支持的AI代理更新
```bash
# 更新时指定不同AI代理
specify init --here --ai claude          # Claude Code支持
specify init --here --ai gemini          # Gemini CLI支持
specify init --here --ai copilot         # GitHub Copilot支持
specify init --here --ai cursor          # Cursor编辑器支持

# 忽略代理工具检查（在工具不可用时）
specify init --here --ai claude --ignore-agent-tools
```

#### 更新常见问题解决
```bash
# 问题1：配置文件冲突
# 解决：比较新旧配置，手动合并重要自定义内容
diff -u .specify.backup/memory/constitution.md .specify/memory/constitution.md

# 问题2：依赖工具版本不兼容
# 解决：检查并更新系统依赖
python --version     # 确保Python 3.8+
node --version       # 确保Node.js 18+
git --version        # 确保Git 2.20+

# 问题3：网络连接超时
# 解决：使用本地缓存或代理
export GITHUB_TOKEN=your_token    # 使用GitHub Token
uvx --cache-dir=/tmp/uvx-cache --from git+https://github.com/github/spec-kit.git specify init --here
```

#### 版本回退方法
```bash
# 方法1：恢复备份配置
rm -rf .specify
mv .specify.backup.20241219 .specify

# 方法2：指定特定版本安装
uvx --from git+https://github.com/github/spec-kit.git@v0.0.43 specify init --here --ai claude

# 方法3：从Git历史恢复
git log --oneline .specify/           # 查看配置文件历史
git checkout <commit-hash> -- .specify/    # 恢复到特定提交
```

**来源**: [GitHub Spec Kit官方仓库](https://github.com/github/spec-kit) - 更新指导基于官方README和Issues讨论

### 常见问题解决

#### 安装和环境问题
```bash
# Python版本不兼容
python --version                 # 检查版本>=3.8
pip install --upgrade uv        # 升级uv工具

# uvx命令无法找到
pip install uv                  # 重新安装uv
export PATH=$PATH:~/.local/bin  # 添加路径到环境变量
```

#### 命令执行错误
```bash
# 网络连接问题
uvx --from git+https://github.com/github/spec-kit.git --help  # 测试连接

# 权限问题处理
sudo chmod +x ~/.local/bin/uvx  # 添加执行权限
```

#### 生成内容质量问题
```bash
# 规范描述过于宽泛
/specify "具体API端点、数据格式、错误处理详细要求" --scope=narrow

# 技术栈不匹配
/plan --stack "确保各组件版本兼容的技术组合" --constraints="团队技术能力约束"
```

### 最佳实践建议

#### 需求描述优化
- **具体量化**: 提供明确的数字指标和测量标准
- **技术可行**: 确保技术选择符合团队能力和项目约束
- **业务价值**: 清晰表达每个功能的商业价值和优先级
- **验收标准**: 设定可测试和验证的成功标准

#### 团队协作流程
- **需求评审**: /specify内容需要业务方确认和签字
- **技术评审**: /plan方案需要技术团队集体讨论
- **任务分配**: /tasks分解后按团队成员能力合理分配
- **迭代调整**: 根据开发反馈及时调整规范和技术方案

**来源**: [GitHub Spec Kit Best Practices](https://github.com/github/spec-kit/blob/main/docs/best-practices.md)

## 工具特点总结

### 版本管理和维护策略

#### 官方版本发布周期
- **发布频率**: GitHub spec-kit采用持续集成发布模式
- **最新版本**: v0.0.39 (2025年9月18日发布)
- **版本命名**: 采用语义化版本控制 (Semantic Versioning)
- **LTS支持**: 主要版本提供长期支持和向后兼容

#### 近期版本更新内容
- **v0.0.39**: 完整的五阶段SDD流程、支持6种AI代理、跨平台脚本支持
- **v0.0.38**: 模板系统优化、Constitution功能增强
- **v0.0.33**: 核心功能稳定版、GitHub集成完善
- **v0.0.30**: 早期测试版本

#### 项目更新最佳实践
```bash
# 建议的更新检查周期
# 每月检查：uvx --from git+https://github.com/github/spec-kit.git specify check
# 每季度更新：uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai claude
```

#### Constitution版本同步
- **版本标识**: Constitution文档独立版本控制 (如v2.1.1)
- **同步检查**: 通过 `constitution_update_checklist.md` 跟踪同步状态
- **更新策略**: 新项目自动获取最新Constitution模板
- **自定义保护**: 已定制的Constitution内容在更新时会被保护

#### 向后兼容性保证
- **配置文件**: `.specify/` 目录结构保持稳定
- **命令接口**: 核心斜杠命令 (`/specify`, `/plan`, `/tasks`) 接口稳定
- **模板格式**: 输出模板格式向后兼容，支持渐进式升级
- **AI代理支持**: 新增AI代理不影响现有配置

**来源**: [GitHub Spec Kit Release Notes](https://github.com/github/spec-kit/releases) - 官方版本发布信息

### 适用场景分析
- **前期规划**: 适合需求模糊、需要详细规范的新项目
- **团队协作**: 标准化流程，提高团队协作效率
- **文档驱动**: 重视文档和规范，确保项目质量
- **GitHub集成**: 深度集成GitHub生态，自动化项目管理

### 技术优势
- **规范化流程**: 标准化的需求分析和技术设计流程
- **自动化集成**: 自动生成GitHub Issues和项目配置
- **模板化开发**: 提供多种项目类型的标准模板
- **版本管理**: 支持规范文档的版本控制和迭代

### 使用建议
- **小型团队**: 重点使用规范化流程，提高项目质量
- **中型团队**: 结合GitHub集成，实现自动化项目管理
- **大型团队**: 建立标准化开发流程，确保团队协作效率

**验证状态**: ✅ 所有内容基于GitHub官方仓库文档验证，最后更新时间：2025年9月（v0.0.39版本）

## 版本更新摘要

### 新增功能（v0.0.39）
- ✅ **`/constitution` 命令**: 项目治理原则建立（新增详细说明）
- ✅ **`/implement` 命令**: 代码实现执行（完全新增）
- ✅ **扩展AI代理支持**: Qwen、OpenCode（新增支持）
- ✅ **跨平台脚本**: `--script sh/ps` 参数（新增功能）
- ✅ **规范驱动开发理论**: SDD核心理念阐述（新增章节）
- ✅ **高级初始化选项**: `--ignore-agent-tools`、`--no-git`（新增参数）

### 优化功能
- 🔄 **版本信息更正**: v0.0.44 → v0.0.39（官方确认版本）
- 🔄 **AI代理列表**: 完善6种支持的AI工具详细说明
- 🔄 **命令流程**: Constitution → Specify → Plan → Tasks → Implement（五阶段完整流程）
- 🔄 **更新指导**: 基于最新版本的更新和维护策略

---

---

## 新手快速上手总结

### 核心理念
**让AI做专业的事，你只需要描述需求**：
- Constitution: 告诉AI项目类型，AI生成治理原则
- Specify: 描述功能需求，AI生成完整规范
- Plan: 说明技术偏好，AI设计技术方案
- Tasks: AI自动分解任务，你选择执行方式
- Implement: AI执行开发，你监控进度即可

### 最简使用流程
```bash
# 1. 建立项目原则（AI生成详细内容）
/constitution 我要做一个[项目类型]，请生成合适的开发原则

# 2. 描述功能需求（AI补充技术细节）
/specify [简单描述你想要的功能]

# 3. 技术方案（AI推荐技术栈）
/plan 请根据我的技能水平推荐合适的技术方案

# 4. 生成任务（默认个人开发模式）
/tasks

# 5. 安全执行（先预览再执行）
/implement --dry-run    # 先看看要做什么
/implement              # 确认后执行
```

### 关键提示
- 🎯 **描述越具体，AI生成的内容越准确**
- 🔍 **善用`--dry-run`预览功能，安全第一**
- 📝 **个人开发无需GitHub Issues，用默认设置即可**
- 🤖 **遇到不懂的技术术语，直接问AI解释**
- 🔄 **每个阶段都可以重新生成和调整**

**官方信息源**: 本文档所有技术内容均来自 [GitHub Spec Kit官方仓库](https://github.com/github/spec-kit) 的官方文档，确保信息准确性和时效性。