# GNOME Wayland Active Window Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 GNOME Wayland 环境下恢复基础活动窗口追踪，返回 `app_name + window_title`，其余 Wayland 桌面继续明确降级。

**Architecture:** Linux 活动窗口入口先按 `X11 / Wayland` 分流，再按 Wayland 桌面环境分流到 GNOME provider。GNOME provider 不再依赖 `org.gnome.Shell.Eval`，而是优先调用公开的 `Focused Window D-Bus` 扩展接口并解析返回的 JSON 字符串。

**Tech Stack:** Rust、Tauri、Node `--test`、GNOME Shell D-Bus、`gdbus`

---

### Task 1: 补齐 Linux 桌面环境识别与计划约束测试

**Files:**
- Modify: `src-tauri/linuxWaylandSupport.test.js`
- Modify: `src/routes/about/About.test.js`
- Modify: `src-tauri/src/linux_session.rs`

- [ ] **Step 1: 写失败测试，约束桌面环境识别与 GNOME provider 分流**

在 `src-tauri/linuxWaylandSupport.test.js` 新增断言：

```js
assert.match(source, /pub enum LinuxDesktopEnvironment/);
assert.match(source, /Gnome/);
assert.match(source, /XDG_CURRENT_DESKTOP/);
assert.match(source, /DESKTOP_SESSION/);
assert.match(source, /get_active_window_linux_wayland_gnome/);
assert.match(source, /org\.gnome\.shell\.extensions\.FocusedWindow\.Get/);
```

- [ ] **Step 2: 运行测试确认失败**

Run: `node --test src-tauri/linuxWaylandSupport.test.js src/routes/about/About.test.js`
Expected: FAIL，提示 `LinuxDesktopEnvironment`、`get_active_window_linux_wayland_gnome` 或新文案键尚不存在

- [ ] **Step 3: 为 linux_session.rs 增加桌面环境枚举与纯函数检测入口**

目标代码结构：

```rust
pub enum LinuxDesktopEnvironment {
    Gnome,
    Kde,
    Sway,
    Hyprland,
    Unknown,
}

fn detect_linux_desktop_environment(
    xdg_current_desktop: Option<&str>,
    desktop_session: Option<&str>,
) -> LinuxDesktopEnvironment
```

- [ ] **Step 4: 运行测试确认通过**

Run: `node --test src-tauri/linuxWaylandSupport.test.js src/routes/about/About.test.js`
Expected: 相关新增断言转绿，其余旧断言继续通过


### Task 2: 先写 Rust 侧失败测试，约束 GNOME Focused Window D-Bus 解析

**Files:**
- Modify: `src-tauri/src/monitor.rs`

- [ ] **Step 1: 写 Rust 单元测试，覆盖 gdbus 输出解析**

在 `src-tauri/src/monitor.rs` 的测试模块新增：

```rust
#[test]
fn gnome_focused_window_dbus输出应解析为活动窗口() {
    let output = "('{\"title\":\"OpenAI Docs - Firefox\",\"wm_class\":\"firefox\",\"wm_class_instance\":\"firefox\"}',)";
    let window = parse_gnome_focused_window_dbus_output(output).expect("应解析成功");
    assert_eq!(window.window_title, "OpenAI Docs - Firefox");
    assert_eq!(window.app_name, "Firefox");
    assert_eq!(window.browser_url, None);
    assert_eq!(window.window_bounds, None);
}

#[test]
fn gnome_focused_window_dbus空对象应视为无活动窗口() {
    assert!(parse_gnome_focused_window_dbus_output(\"('{}',)\").is_err());
}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cargo test --manifest-path src-tauri/Cargo.toml monitor::tests::gnome_focused_window_dbus`
Expected: FAIL，提示解析函数不存在

- [ ] **Step 3: 仅实现最小解析函数与归一化映射**

目标代码结构：

```rust
#[cfg(any(target_os = "linux", test))]
fn parse_gnome_focused_window_dbus_output(output: &str) -> Result<ActiveWindow> { ... }
```

实现要求：

- 从 `gdbus call` 输出里截取首个 `{...}` JSON 片段
- 读取 `title`、`wm_class`、`wm_class_instance`
- `app_name` 优先使用 `wm_class`，再走 `normalize_display_app_name`
- 其他字段固定为 `None`

- [ ] **Step 4: 运行测试确认通过**

Run: `cargo test --manifest-path src-tauri/Cargo.toml monitor::tests::gnome_focused_window_dbus`
Expected: PASS


### Task 3: 接入 GNOME Wayland provider

**Files:**
- Modify: `src-tauri/src/monitor.rs`
- Modify: `src-tauri/src/linux_session.rs`

- [ ] **Step 1: 写失败测试，约束 Linux get_active_window 分发**

在 `src-tauri/linuxWaylandSupport.test.js` 增加断言：

```js
assert.match(source, /current_linux_desktop_environment/);
assert.match(source, /LinuxDesktopEnvironment::Gnome/);
assert.match(source, /get_active_window_linux_x11/);
assert.match(source, /get_active_window_linux_wayland_gnome/);
```

- [ ] **Step 2: 运行测试确认失败**

Run: `node --test src-tauri/linuxWaylandSupport.test.js`
Expected: FAIL，提示函数名或分流逻辑缺失

- [ ] **Step 3: 把现有 X11 逻辑抽成独立函数，并新增 GNOME Wayland provider**

目标结构：

```rust
fn get_active_window_linux_x11() -> Result<ActiveWindow> { ... }

fn get_active_window_linux_wayland_gnome() -> Result<ActiveWindow> { ... }

pub fn get_active_window() -> Result<ActiveWindow> {
    match current_linux_desktop_session() {
        LinuxDesktopSession::X11 => get_active_window_linux_x11(),
        LinuxDesktopSession::Wayland => { ... }
        LinuxDesktopSession::Unknown => ...
    }
}
```

GNOME provider 调用命令：

```bash
gdbus call --session \
  --dest org.gnome.Shell \
  --object-path /org/gnome/shell/extensions/FocusedWindow \
  --method org.gnome.shell.extensions.FocusedWindow.Get
```

- [ ] **Step 4: 运行测试确认通过**

Run: `node --test src-tauri/linuxWaylandSupport.test.js`
Expected: PASS


### Task 4: 明确 GNOME Wayland 的降级文案与可用性探测

**Files:**
- Modify: `src-tauri/src/commands.rs`
- Modify: `src/routes/about/About.svelte`
- Modify: `src/lib/i18n/index.js`
- Modify: `src/routes/about/About.test.js`

- [ ] **Step 1: 写失败测试，约束关于页状态文案分支**

在 `src/routes/about/About.test.js` 增加断言：

```js
assert.match(source, /about\.linuxSessionGnomeWaylandReady/);
assert.match(source, /desktopEnvironment/);
assert.match(source, /sessionType === 'wayland'/);
```

- [ ] **Step 2: 运行测试确认失败**

Run: `node --test src/routes/about/About.test.js`
Expected: FAIL，提示新 key 或前端分支尚不存在

- [ ] **Step 3: 扩展 get_linux_session_support 返回桌面环境与 provider 可用性**

目标结构：

```rust
pub struct LinuxSessionSupportInfo {
    pub platform: String,
    pub session_type: String,
    pub desktop_environment: String,
    pub active_window_supported: bool,
    pub screenshot_supported: bool,
}
```

Wayland 下 `active_window_supported` 判断规则：

- `GNOME` 且 `FocusedWindow.Get` 调用成功：`true`
- 其他情况：`false`

- [ ] **Step 4: 更新关于页与多语言文案**

前端要求：

- `X11` 使用现有 ready 文案
- `GNOME Wayland + supported=true` 使用新的 ready 文案
- 其他 Wayland 继续显示 pending / warning

- [ ] **Step 5: 运行测试确认通过**

Run: `node --test src/routes/about/About.test.js`
Expected: PASS


### Task 5: 端到端验证本次改动相关模块

**Files:**
- Modify: `src-tauri/linuxWaylandSupport.test.js`
- Modify: `src-tauri/src/monitor.rs`
- Modify: `src-tauri/src/linux_session.rs`

- [ ] **Step 1: 跑 Node 静态测试**

Run: `node --test src-tauri/linuxWaylandSupport.test.js src/routes/about/About.test.js`
Expected: PASS

- [ ] **Step 2: 跑 Rust 监控模块测试**

Run: `cargo test --manifest-path src-tauri/Cargo.toml monitor::tests`
Expected: 新增 GNOME Wayland 解析测试通过；若存在历史无关失败，需要单独记录

- [ ] **Step 3: 跑 Rust Linux 会话相关测试**

Run: `cargo test --manifest-path src-tauri/Cargo.toml linux_session`
Expected: PASS 或 0 tests / 0 failed

- [ ] **Step 4: 跑截图与空闲检测回归**

Run: `cargo test --manifest-path src-tauri/Cargo.toml screenshot::tests idle_detector::tests`
Expected: PASS

- [ ] **Step 5: 记录本次实现边界**

实现完成后在结果中明确写出：

- GNOME Wayland 活动窗口追踪依赖 `Focused Window D-Bus` 扩展接口
- 本阶段仍未恢复 `browser_url`
- 本阶段仍未恢复 `window_bounds`
