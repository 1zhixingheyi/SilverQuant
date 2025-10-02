-- SilverQuant 数据存储优化 - MySQL 初始化脚本
-- 创建数据库和表结构
-- 生成时间: 2025-10-01

-- 使用数据库
USE silverquant;

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER_SET_CLIENT = utf8mb4;

-- ============================================================
-- 1. Account (账户表) - WARM层
-- ============================================================
CREATE TABLE IF NOT EXISTS account (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '内部ID',
    account_id VARCHAR(50) NOT NULL UNIQUE COMMENT '账户ID(对应QMT_ACCOUNT_ID)',
    account_name VARCHAR(100) NOT NULL COMMENT '账户名称',
    broker VARCHAR(50) NOT NULL COMMENT '券商(QMT/GM/TDX)',
    initial_capital DECIMAL(20,2) NOT NULL COMMENT '初始资金(元)',
    current_capital DECIMAL(20,2) DEFAULT NULL COMMENT '当前资金(元)',
    total_assets DECIMAL(20,2) DEFAULT NULL COMMENT '总资产(元)',
    position_value DECIMAL(20,2) DEFAULT NULL COMMENT '持仓市值(元)',
    status ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 约束
    CONSTRAINT chk_account_id_len CHECK (CHAR_LENGTH(account_id) BETWEEN 6 AND 50),
    CONSTRAINT chk_initial_capital CHECK (initial_capital > 0),
    CONSTRAINT chk_current_capital CHECK (current_capital IS NULL OR current_capital >= 0),
    CONSTRAINT chk_broker CHECK (broker IN ('QMT', 'GM', 'TDX')),

    -- 索引
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易账户表';

-- ============================================================
-- 2. Strategy (策略表) - WARM层
-- ============================================================
CREATE TABLE IF NOT EXISTS strategy (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '内部ID',
    strategy_name VARCHAR(100) NOT NULL UNIQUE COMMENT '策略名称',
    strategy_code VARCHAR(50) NOT NULL UNIQUE COMMENT '策略代码(英文标识)',
    strategy_type ENUM('wencai', 'remote', 'technical') NOT NULL COMMENT '策略类型',
    version VARCHAR(20) NOT NULL COMMENT '版本号',
    status ENUM('active', 'testing', 'inactive') NOT NULL DEFAULT 'active' COMMENT '状态',
    description TEXT DEFAULT NULL COMMENT '策略描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 约束
    CONSTRAINT chk_strategy_name_len CHECK (CHAR_LENGTH(strategy_name) BETWEEN 3 AND 100),
    CONSTRAINT chk_strategy_code_format CHECK (strategy_code REGEXP '^[a-z0-9_]+$'),

    -- 索引
    INDEX idx_strategy_type (strategy_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易策略表';

-- ============================================================
-- 3. AccountStrategy (账户-策略关联表) - WARM层
-- ============================================================
CREATE TABLE IF NOT EXISTS account_strategy (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '内部ID',
    account_id INT NOT NULL COMMENT '账户ID',
    strategy_id INT NOT NULL COMMENT '策略ID',
    allocated_capital DECIMAL(20,2) NOT NULL COMMENT '分配资金(元)',
    risk_limit DECIMAL(5,2) NOT NULL COMMENT '风险限额(百分比)',
    status ENUM('active', 'paused') NOT NULL DEFAULT 'active' COMMENT '绑定状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 约束
    CONSTRAINT chk_allocated_capital CHECK (allocated_capital > 0),
    CONSTRAINT chk_risk_limit CHECK (risk_limit >= 0 AND risk_limit <= 100),
    UNIQUE KEY uk_account_strategy (account_id, strategy_id),

    -- 外键
    CONSTRAINT fk_account_strategy_account FOREIGN KEY (account_id) REFERENCES account(id) ON DELETE CASCADE,
    CONSTRAINT fk_account_strategy_strategy FOREIGN KEY (strategy_id) REFERENCES strategy(id) ON DELETE CASCADE,

    -- 索引
    INDEX idx_account_id (account_id),
    INDEX idx_strategy_id (strategy_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='账户-策略关联表';

-- ============================================================
-- 4. StrategyParam (策略参数表) - WARM层
-- ============================================================
CREATE TABLE IF NOT EXISTS strategy_param (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '内部ID',
    strategy_id INT NOT NULL COMMENT '所属策略ID',
    param_key VARCHAR(100) NOT NULL COMMENT '参数键',
    param_value TEXT NOT NULL COMMENT '参数值(JSON格式)',
    param_type ENUM('int', 'float', 'string', 'json') NOT NULL COMMENT '参数类型',
    version INT NOT NULL COMMENT '版本号',
    is_active BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否为当前激活版本',
    remark VARCHAR(200) DEFAULT NULL COMMENT '版本备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 约束
    UNIQUE KEY uk_strategy_param_version (strategy_id, param_key, version),

    -- 外键
    CONSTRAINT fk_strategy_param_strategy FOREIGN KEY (strategy_id) REFERENCES strategy(id) ON DELETE CASCADE,

    -- 索引
    INDEX idx_strategy_id (strategy_id),
    INDEX idx_param_key (param_key),
    INDEX idx_is_active (is_active),
    INDEX idx_version (version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='策略参数表';

-- ============================================================
-- 5. User (用户表) - WARM层
-- ============================================================
CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '内部ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希(bcrypt)',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    real_name VARCHAR(100) DEFAULT NULL COMMENT '真实姓名',
    status ENUM('active', 'inactive', 'locked') NOT NULL DEFAULT 'active' COMMENT '状态',
    last_login_at TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间',
    last_login_ip VARCHAR(45) DEFAULT NULL COMMENT '最后登录IP',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 约束
    CONSTRAINT chk_username_len CHECK (CHAR_LENGTH(username) BETWEEN 3 AND 50),
    CONSTRAINT chk_username_format CHECK (username REGEXP '^[a-zA-Z0-9_]+$'),
    CONSTRAINT chk_email_format CHECK (email REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'),

    -- 索引
    INDEX idx_status (status),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================
-- 6. Role (角色表) - WARM层
-- ============================================================
CREATE TABLE IF NOT EXISTS role (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '内部ID',
    role_name VARCHAR(50) NOT NULL UNIQUE COMMENT '角色名称',
    role_code VARCHAR(50) NOT NULL UNIQUE COMMENT '角色代码',
    description VARCHAR(200) DEFAULT NULL COMMENT '角色描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 索引
    INDEX idx_role_code (role_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- ============================================================
-- 7. Permission (权限表) - WARM层
-- ============================================================
CREATE TABLE IF NOT EXISTS permission (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '内部ID',
    permission_name VARCHAR(100) NOT NULL UNIQUE COMMENT '权限名称',
    permission_code VARCHAR(100) NOT NULL UNIQUE COMMENT '权限代码',
    resource_type VARCHAR(50) NOT NULL COMMENT '资源类型',
    action_type ENUM('create', 'read', 'update', 'delete', 'manage') NOT NULL COMMENT '操作类型',
    description VARCHAR(200) DEFAULT NULL COMMENT '权限描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 索引
    INDEX idx_permission_code (permission_code),
    INDEX idx_resource_type (resource_type),
    INDEX idx_action_type (action_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

-- ============================================================
-- 8. UserRole (用户-角色关联表)
-- ============================================================
CREATE TABLE IF NOT EXISTS user_role (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '内部ID',
    user_id INT NOT NULL COMMENT '用户ID',
    role_id INT NOT NULL COMMENT '角色ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',

    -- 约束
    UNIQUE KEY uk_user_role (user_id, role_id),

    -- 外键
    CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_role_role FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE,

    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_role_id (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户-角色关联表';

-- ============================================================
-- 9. RolePermission (角色-权限关联表)
-- ============================================================
CREATE TABLE IF NOT EXISTS role_permission (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '内部ID',
    role_id INT NOT NULL COMMENT '角色ID',
    permission_id INT NOT NULL COMMENT '权限ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',

    -- 约束
    UNIQUE KEY uk_role_permission (role_id, permission_id),

    -- 外键
    CONSTRAINT fk_role_permission_role FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permission_permission FOREIGN KEY (permission_id) REFERENCES permission(id) ON DELETE CASCADE,

    -- 索引
    INDEX idx_role_id (role_id),
    INDEX idx_permission_id (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色-权限关联表';

-- ============================================================
-- 插入预定义角色
-- ============================================================
INSERT INTO role (role_name, role_code, description) VALUES
('管理员', 'admin', '所有权限'),
('策略开发', 'developer', '策略配置、参数管理'),
('交易员', 'trader', '查看持仓、交易记录'),
('只读用户', 'viewer', '仅查看权限')
ON DUPLICATE KEY UPDATE role_name=VALUES(role_name);

-- ============================================================
-- 插入预定义权限
-- ============================================================
INSERT INTO permission (permission_name, permission_code, resource_type, action_type, description) VALUES
-- 账户权限
('查看账户', 'account:read', 'account', 'read', '查看账户信息'),
('创建账户', 'account:create', 'account', 'create', '创建新账户'),
('更新账户', 'account:update', 'account', 'update', '更新账户信息'),
('删除账户', 'account:delete', 'account', 'delete', '删除账户'),
-- 策略权限
('查看策略', 'strategy:read', 'strategy', 'read', '查看策略信息'),
('管理策略', 'strategy:manage', 'strategy', 'manage', '管理策略(含创建/更新/删除)'),
-- 交易权限
('查看交易记录', 'trade:read', 'trade', 'read', '查看交易记录'),
('执行交易', 'trade:execute', 'trade', 'create', '执行交易操作')
ON DUPLICATE KEY UPDATE permission_name=VALUES(permission_name);

-- ============================================================
-- 分配权限给角色
-- ============================================================
-- admin: 所有权限
INSERT INTO role_permission (role_id, permission_id)
SELECT r.id, p.id FROM role r, permission p WHERE r.role_code = 'admin'
ON DUPLICATE KEY UPDATE role_id=VALUES(role_id);

-- developer: 策略管理权限
INSERT INTO role_permission (role_id, permission_id)
SELECT r.id, p.id FROM role r, permission p
WHERE r.role_code = 'developer' AND p.permission_code IN ('strategy:read', 'strategy:manage', 'account:read')
ON DUPLICATE KEY UPDATE role_id=VALUES(role_id);

-- trader: 交易和查看权限
INSERT INTO role_permission (role_id, permission_id)
SELECT r.id, p.id FROM role r, permission p
WHERE r.role_code = 'trader' AND p.permission_code IN ('account:read', 'strategy:read', 'trade:read', 'trade:execute')
ON DUPLICATE KEY UPDATE role_id=VALUES(role_id);

-- viewer: 仅查看权限
INSERT INTO role_permission (role_id, permission_id)
SELECT r.id, p.id FROM role r, permission p
WHERE r.role_code = 'viewer' AND p.permission_code IN ('account:read', 'strategy:read', 'trade:read')
ON DUPLICATE KEY UPDATE role_id=VALUES(role_id);

-- ============================================================
-- 插入测试数据
-- ============================================================
-- 测试账户
INSERT INTO account (account_id, account_name, broker, initial_capital, current_capital, total_assets, status) VALUES
('55009728', '生产账户', 'QMT', 1000000.00, 980000.00, 1050000.00, 'active')
ON DUPLICATE KEY UPDATE account_name=VALUES(account_name);

-- 测试策略
INSERT INTO strategy (strategy_name, strategy_code, strategy_type, version, status, description) VALUES
('问财选股V1', 'wencai_v1', 'wencai', '1.0.0', 'active', '基于问财条件选股的策略')
ON DUPLICATE KEY UPDATE strategy_name=VALUES(strategy_name);

-- 完成
SELECT 'MySQL初始化完成' AS status,
       (SELECT COUNT(*) FROM account) AS accounts,
       (SELECT COUNT(*) FROM strategy) AS strategies,
       (SELECT COUNT(*) FROM role) AS roles,
       (SELECT COUNT(*) FROM permission) AS permissions;
