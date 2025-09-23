%23 Docker 桌面版排故记录（Windows/WSL）

> 本文用于沉淀本次对话中的问题解决过程与方法、结果以及后续工作，便于复盘与复用。若与实际对话存在偏差，请在“待补充”处完善具体细节。

- 会话ID: `bc5a899b-4d8a-4187-b01b-dc4fac239eeb`
- 记录角色: Codex 助手
- 适用范围: Docker Desktop（Windows/WSL 环境）的一般性排障流程与本次实战记录

---

## 一、问题背景与症状
- 触发时间: [待补充]
- 运行环境: [待补充，例如 Windows 11 + Docker Desktop + WSL2]
- 相关组件: [待补充，例如 Docker Engine、WSL2、Hyper-V、网络代理、镜像仓库]
- 现象描述: [待补充，例如 Docker Desktop 无法启动 / Engine 未运行 / 拉取镜像失败 / 容器无法联网 / CPU 飙高等]
- 影响范围: [待补充]

## 二、排故目标
- 目标状态: [待补充，例如 恢复 Docker Desktop 正常启动与容器运行能力]
- 验收标准:
  - `docker info` 正常返回且无错误
  - 能成功 `docker run hello-world`
  - 能正常拉取企业镜像源/私有仓库镜像（如适用）

## 三、过程与方法（基于本对话）
> 注：以下为结构化复盘清单；方括号为本次对话中的具体结论或数据，请据实补充。

1) 明确问题与假设
- 收敛症状与范围，建立候选根因清单：[待补充]
- 初步假设（示例）：WSL 集成异常 / 后台服务未启动 / 代理配置导致网络不可达 / 虚拟化组件冲突 / 升级残留/缓存损坏

2) 收集诊断信息（已执行）
- Docker Desktop 面板：Troubleshoot 导出支持包（诊断包）：[尚未生成，因未安装]
- 基本命令输出：
  - `docker version`：未找到 docker 命令（未安装或未入 PATH）
  - `docker info`：同上，未执行
 - `wsl -l -v`：存在发行版 Ubuntu-22.04，状态 Stopped，Version=2（字符编码显示异常，但信息可辨）
  - `wsl.exe --status`：命令执行成功（编码异常，内容未粘贴）
  - `netsh interface ip show config`：未执行（暂未发现网络相关报错）
- 系统日志/事件查看器（可选）：未查看

3) 验证与定位（按影响面由外至内）
- 网络连通性：DNS/代理/仓库可达性验证：[待补充]
- 引擎与后端：`com.docker.service`/`com.docker.backend` 状态验证：[待补充]
- WSL/Hyper-V：虚拟化开启、WSL 内核版本、发行版状态：[待补充]
- 配置与缓存：`~/.docker`、镜像/卷、Builder 缓存健康度：[待补充]

4) 修复动作（最小可行变更，逐步升级强度）
- 软修复
  - 重启 Docker Desktop / 后台服务 / WSL 子系统：`wsl --shutdown`、`Restart-Service com.docker.service`：[待补充执行结果]
    - 已执行：`wsl --shutdown` → 成功
  - `Get-Service com.docker.service`：未找到（未安装 Docker Desktop）
  - 清理网络栈（如需）：`netsh winsock reset` + 重启：[待补充]
  - 调整/移除代理设置（如配置了 HTTP(S)_PROXY）：[待补充]
- 中强度修复
  - 重新启用 WSL 集成（Docker Desktop Settings → Resources → WSL Integration）：[待补充]
  - 重新安装/修复 WSL 内核/发行版（保留数据）：[待补充]
  - 清理 Docker Desktop 缓存（不删除业务卷/镜像，谨慎）：[待补充]
- 强修复（需评估与备份）
  - Docker Desktop Factory Reset（出厂重置）：[待补充]
  - 彻底卸载并重装（含清理残留目录/注册表，先备份卷/镜像）：[待补充]

已尝试安装动作
- `winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements --silent`
  - 结果：安装未成功（退出码=1）。常见原因：缺少管理员权限/需要交互或系统层组件安装。
  - 检查：`winget list --id Docker.DockerDesktop` 显示未安装。
  - 建议：以管理员 PowerShell 重新执行安装命令；若仍失败，使用 Docker Desktop 安装包手动安装并保存安装日志。

本地组与权限检查（已执行）
- `net localgroup docker-users`：组存在，但成员列表为空
- 当前用户：`DESKTOP-E339HPJ\liuyan`
- 非管理员环境下尝试加入组：`net localgroup docker-users DESKTOP-E339HPJ\liuyan /add` → 结果：System error 5（访问被拒绝）
- 结论：需在“管理员 PowerShell”中先把当前用户加入 `docker-users` 组，再重新安装

5) 回归与验证
- `docker run --rm hello-world` 成功：[未验证，因未安装]
- 关键业务镜像拉取、容器启动、网络访问、挂载卷读写验证：[未验证]
- 性能与稳定性观察（CPU/内存/IO）：[未验证]

## 四、结果
- 处置结论： 未完成安装（Docker Desktop 未安装，服务不存在）
- 根因定位： 需要管理员权限以安装 Docker Desktop（或使用交互式安装）
- 证据与佐证：
  - `docker version`：CommandNotFound（未安装/未入 PATH）
  - `Get-Service com.docker.service`：服务不存在
  - `winget list --id Docker.DockerDesktop`：未安装
  - `wsl -l -v`：Ubuntu-22.04 可用（Stopped, Version=2）
  - `net localgroup docker-users`：组存在但无成员；非管理员添加成员返回 System error 5

## 五、后续工作（Action Items）
- 防回归
  - 建立“启动自检脚本”：统一收集 `docker info/version`、`wsl` 状态、代理和网络检测 → 输出健康报告
  - 在 CI 或本地 `make doctor` 中集成关键自检（如适用）
- 运维与文档
  - 以管理员身份执行安装：管理员 PowerShell 运行
    - `winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements`
  - 若 `winget` 安装失败：使用 Docker 官网安装包手动安装，并开启安装日志；安装完成后确认 `com.docker.service` 存在且运行
  - 先手动把当前用户加入 `docker-users` 组（需管理员）：
    ```powershell
    # 以管理员 PowerShell 执行
    $id=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    net localgroup docker-users /add  # 如果提示不存在则创建
    net localgroup docker-users "$id" /add
    net localgroup docker-users       # 验证成员中包含当前账号
    ```
  - 加入组后建议先注销/重启，再进行安装或启动 Docker Desktop
  - 将本次诊断包/日志归档至 `docs/troubleshooting/docker/<yyyyMMdd>/`：[待补充]
  - 完善公司环境下的代理/镜像源配置指引（含白名单与排除规则）：[待补充]
  - 增补常见错误码与对照表（如 403/TLS/Name resolution 等）：[待补充]
- 工具化与自动化
  - 提供一键修复脚本选项（软修复集合），加强“可回滚”与“交互确认”
  - 加入 WSL 发行版健康检查与一键重建辅助（保留数据前提）

## 六、常用命令速查（Windows/WSL）
```powershell
# 查看 Docker / 环境
docker version
docker info

# 简单连通性与拉取测试
docker run --rm hello-world

# WSL 状态与控制
wsl -l -v
wsl --status
wsl --shutdown

# 重启 Docker 后台服务（以管理员 PowerShell）
Get-Service com.docker.service | Restart-Service -Force

# 代理变量清理（示例，按需执行）
[System.Environment]::SetEnvironmentVariable("HTTP_PROXY", $null, "User")
[System.Environment]::SetEnvironmentVariable("HTTPS_PROXY", $null, "User")
[System.Environment]::SetEnvironmentVariable("NO_PROXY", $null, "User")
```

## 八、常见错误与修复
- 安装失败：Component Docker.Installer.AddToGroupAction failed: 调用的目标发生了异常
  - 现象：winget 安装 Docker Desktop 失败，日志提示 AddToGroupAction（安装过程中将当前用户加入本地组 docker-users）异常。
  - 可能原因：
    - 非管理员安装，导致无法创建/修改本地用户组
    - 机器加入域/Azure AD，主体名解析异常或权限受限
    - 本地组 `docker-users` 不存在或损坏
  - 处理步骤（管理员 PowerShell 执行）：
    - 创建本地组（如不存在）：
      ```powershell
      Import-Module Microsoft.PowerShell.LocalAccounts
      if (-not (Get-LocalGroup -Name 'docker-users' -ErrorAction SilentlyContinue)) {
        New-LocalGroup -Name 'docker-users' -Description 'Users allowed to run Docker Desktop'
      }
      ```
    - 将当前用户加入组：
      ```powershell
      $me = (whoami)
      Add-LocalGroupMember -Group 'docker-users' -Member $me -ErrorAction SilentlyContinue
      net localgroup docker-users
      ```
      - 若为域/云账号：可尝试 `AzureAD\user@domain.com` 或 `DOMAIN\username` 格式
      - 备用（纯 net 命令）：
        ```powershell
        net localgroup docker-users /add  # 组不存在时
        net localgroup docker-users "%USERDOMAIN%\%USERNAME%" /add
        ```
    - 重新以管理员安装：
      ```powershell
      winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
      ```
    - 安装后建议重启或注销登录，使组成员身份生效
  - 日志位置：
    - winget 日志：`%LOCALAPPDATA%\Packages\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe\LocalState\DiagOutputDir\`
    - Docker 安装日志（如有）：`%LOCALAPPDATA%\Docker\install-log-*.txt`

## 七、变更记录
- v0.1 初稿：基于当前对话需求创建结构化排故记录，保留“待补充”占位，等待补全具体证据与结论。
- v0.2：补充安装失败（AddToGroupAction）问题的原因分析与修复步骤；记录 winget 安装尝试与当前环境状态。

---

如需，我可以将本次对话中的具体操作日志、命令输出与截图路径直接补齐到对应“待补充”位置，并整理为可归档的诊断包结构（含 `README.md` 与索引）。
