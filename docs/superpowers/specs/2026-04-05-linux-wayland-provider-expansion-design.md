# Linux Wayland Provider 扩展设计

日期：2026-04-05

## 1. 背景

当前项目已经补齐：

- GNOME Wayland 基础活动窗口追踪
- Linux `window_bounds`
- Linux 截图链路消费 `window_bounds`

但仍有两个缺口：

- `KDE / Sway / Hyprland / 其他 Wayland` 未覆盖
- Linux `browser_url` 仍未恢复

这会导致 issue #51 虽然已有明显进展，但还不足以说明“Wayland 已适配完成”。

## 2. 目标

本阶段目标：

1. 补齐主流 Linux Wayland 桌面环境的活动窗口来源
2. 恢复 Linux 浏览器 URL 的最佳努力采集

## 3. 支持矩阵

### 3.1 活动窗口 provider

- X11：继续使用现有 `xdotool + xprop + getwindowgeometry`
- GNOME Wayland：继续使用 `Focused Window D-Bus`
- KDE Plasma Wayland：新增 KDE provider
- Sway：新增 `swaymsg -t get_tree` provider
- Hyprland：新增 `hyprctl activewindow -j` provider
- Unknown Wayland：按 provider 探测顺序自动尝试

### 3.2 浏览器 URL

- Firefox / Zen / LibreWolf / Waterfox：sessionstore 恢复
- Chromium 系：标题 URL 提取
- 其他浏览器：标题 URL 提取 + 最近活动恢复

## 4. 非目标

- 不承诺所有 Wayland compositor 全覆盖
- 不引入浏览器扩展
- 不引入 Chromium 远程调试依赖
- 不实现“所有浏览器页面 URL 完整恢复”

## 5. 方案选择

### 方案 A：继续按桌面环境硬编码 provider

优点：

- 最直接
- 与现有 Linux session 检测一致

缺点：

- 对未知 Wayland 会话不友好
- 代码扩展性差

### 方案 B：建立 provider 探测链

优点：

- 可以覆盖已知桌面，也能容纳未知会话
- 便于新增 provider
- 对 issue 回复更稳妥，能说“主流 Wayland provider 已接入”

缺点：

- 代码稍复杂

### 推荐

采用 **方案 B**：

- 保留 `desktop environment` 识别，用于优先排序
- 真实调用走 provider 探测链

## 6. 活动窗口 provider 设计

### 6.1 统一返回结构

所有 Linux provider 都返回统一 `ActiveWindow`：

- `app_name`
- `window_title`
- `browser_url`
- `executable_path`
- `window_bounds`

### 6.2 Provider 顺序

#### GNOME

优先条件：

- `desktop_environment == Gnome`

实现：

- `gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/shell/extensions/FocusedWindow --method org.gnome.shell.extensions.FocusedWindow.Get`

#### KDE Plasma

优先条件：

- `desktop_environment == Kde`

实现：

- 优先尝试 `kdotool`
- 读取活动窗口、标题、几何

说明：

- KWin 原生对外暴露稳定“当前活动窗口元数据”的 CLI/DBus 接口不适合作为零配置方案
- 本阶段以 KDE 社区常用工具链为优先 provider

#### Sway

优先条件：

- `desktop_environment == Sway`
- 或 `SWAYSOCK` 存在

实现：

- `swaymsg -t get_tree`
- 遍历 JSON，找到 `focused == true` 的节点
- 读取：
  - `name`
  - `app_id`
  - `pid`
  - `rect`

#### Hyprland

优先条件：

- `desktop_environment == Hyprland`
- 或 `HYPRLAND_INSTANCE_SIGNATURE` 存在

实现：

- `hyprctl activewindow -j`
- 读取：
  - `title`
  - `class`
  - `pid`
  - `at`
  - `size`

### 6.3 Unknown Wayland

如果桌面环境未知，则按顺序尝试：

1. Hyprland provider
2. Sway provider
3. GNOME provider
4. KDE provider

全部失败后返回明确错误。

## 7. Linux 浏览器 URL 设计

### 7.1 统一入口

Linux 下恢复 `resolve_browser_url_for_window(app_name, window_title)`：

- 先判断是否浏览器
- Firefox family 优先走 sessionstore
- 未命中再尝试从标题提取 URL

### 7.2 Firefox family

支持：

- Firefox
- Zen
- LibreWolf
- Waterfox

Linux 常见 profile 根目录：

- `~/.mozilla/firefox`
- `~/.zen`
- `~/.librewolf`
- `~/.waterfox`

实现：

- 复用现有 `profiles.ini + recovery.jsonlz4/sessionstore.jsonlz4` 解析逻辑

### 7.3 Chromium family

本阶段不引入远程调试接口。

实现：

- 从窗口标题提取 URL-like 文本
- 若标题不含 URL，则继续依赖最近活动恢复逻辑

## 8. 错误处理

- provider 启动失败：继续尝试下一个 provider
- provider 输出格式异常：记录 warning，继续尝试下一个 provider
- 所有 provider 失败：返回综合降级错误
- 浏览器 URL 失败：不阻塞活动窗口采集

## 9. 测试设计

### 9.1 Node 源码测试

新增断言覆盖：

- KDE provider
- Sway provider
- Hyprland provider
- Linux 浏览器 URL 恢复入口
- Firefox family Linux profile 根目录

### 9.2 Rust 单元测试

新增解析测试：

- `swaymsg get_tree` focused node 解析
- `hyprctl activewindow -j` 解析
- KDE provider 文本解析
- Linux Firefox family 根目录映射
- Linux browser URL 入口优先级

## 10. 风险

### 10.1 KDE 依赖外部工具

KDE 本阶段将依赖 `kdotool`。

控制方式：

- provider 不可用时继续尝试其他 provider
- 关于页支持状态不再只看桌面环境，还要看 provider 可用性

### 10.2 浏览器 URL 无法完全恢复

Chromium 系在 Wayland 下仍没有可靠零配置方案。

控制方式：

- Firefox family 恢复真实 URL
- Chromium 系恢复“标题 URL + 最近活动兜底”
- 最终对 issue 的说明必须写清这一点

## 11. 完成标准

以下条件全部满足，才认为这轮达到“可关闭 #51”门槛：

1. GNOME / KDE / Sway / Hyprland 都有可执行 provider
2. Unknown Wayland 会自动尝试 provider 链
3. Linux `browser_url` 恢复入口不再固定返回 `None`
4. Node 测试通过
5. Rust 针对性测试通过
