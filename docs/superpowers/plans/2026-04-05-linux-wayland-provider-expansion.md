# Linux Wayland Provider Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补齐 KDE / Sway / Hyprland / Unknown Wayland 的活动窗口 provider，并恢复 Linux 浏览器 URL 的最佳努力采集。

**Architecture:** Linux Wayland 改为 provider 探测链而不是单一桌面硬编码；浏览器 URL 则复用现有 sessionstore 与标题提取逻辑，先恢复 Firefox family，再覆盖 Chromium 标题兜底。

**Tech Stack:** Rust、Node `--test`、gdbus、swaymsg、hyprctl、kdotool

---

### Task 1: 先写失败测试，约束多 Wayland provider 与 Linux browser_url 入口

**Files:**
- Modify: `src-tauri/linuxWaylandSupport.test.js`
- Modify: `src-tauri/src/monitor.rs`

- [ ] **Step 1: 写失败测试**

新增源码断言：

```js
assert.match(source, /get_active_window_linux_wayland_kde/);
assert.match(source, /get_active_window_linux_wayland_sway/);
assert.match(source, /get_active_window_linux_wayland_hyprland/);
assert.match(source, /swaymsg/);
assert.match(source, /hyprctl/);
assert.match(source, /kdotool/);
assert.match(source, /firefox_family_session_store_url_linux/);
assert.match(source, /resolve_browser_url_for_window_linux/);
```

- [ ] **Step 2: 跑测试确认失败**

Run: `node --test src-tauri/linuxWaylandSupport.test.js`
Expected: FAIL

- [ ] **Step 3: 实现最小骨架**

先只补函数名、provider 分发骨架与 Linux browser_url 入口骨架，不做完整逻辑。

- [ ] **Step 4: 跑测试确认通过**

Run: `node --test src-tauri/linuxWaylandSupport.test.js`
Expected: PASS


### Task 2: 补 Sway / Hyprland provider 解析

**Files:**
- Modify: `src-tauri/src/monitor.rs`

- [ ] **Step 1: 写 Rust 失败测试**

新增：

```rust
#[test]
fn sway_get_tree_focused节点应解析为活动窗口() { ... }

#[test]
fn hyprctl_activewindow应解析为活动窗口() { ... }
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cargo test --manifest-path src-tauri/Cargo.toml sway_get_tree hyprctl_activewindow`
Expected: FAIL

- [ ] **Step 3: 实现最小解析**

要求：

- Sway 读取 `name/app_id/pid/rect`
- Hyprland 读取 `title/class/pid/at/size`
- 统一映射到 `ActiveWindow`

- [ ] **Step 4: 跑测试确认通过**

Run: `cargo test --manifest-path src-tauri/Cargo.toml sway_get_tree hyprctl_activewindow`
Expected: PASS


### Task 3: 补 KDE provider

**Files:**
- Modify: `src-tauri/src/monitor.rs`

- [ ] **Step 1: 写失败测试**

新增源码或解析测试，约束 `kdotool` provider 存在。

- [ ] **Step 2: 跑测试确认失败**

Run: `node --test src-tauri/linuxWaylandSupport.test.js`
Expected: FAIL

- [ ] **Step 3: 实现 KDE provider**

要求：

- 调用 `kdotool`
- 获取活动窗口 id / 标题 / 类名 / 几何
- 映射到 `ActiveWindow`

- [ ] **Step 4: 跑测试确认通过**

Run: `node --test src-tauri/linuxWaylandSupport.test.js`
Expected: PASS


### Task 4: 恢复 Linux browser_url

**Files:**
- Modify: `src-tauri/src/monitor.rs`

- [ ] **Step 1: 写失败测试**

新增：

```rust
#[test]
fn linux_firefox_family根目录应按浏览器映射() { ... }

#[test]
fn linux_browser_url入口应优先sessionstore再回退标题提取() { ... }
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cargo test --manifest-path src-tauri/Cargo.toml linux_firefox_family linux_browser_url入口`
Expected: FAIL

- [ ] **Step 3: 实现 Linux browser_url 入口**

要求：

- Linux 不再让 `resolve_browser_url_for_window()` 直接返回 `None`
- Firefox family 走 sessionstore
- 其余浏览器走标题提取

- [ ] **Step 4: 跑测试确认通过**

Run: `cargo test --manifest-path src-tauri/Cargo.toml linux_firefox_family linux_browser_url入口`
Expected: PASS


### Task 5: 全链路回归

**Files:**
- Modify: `src-tauri/src/monitor.rs`
- Modify: `src-tauri/linuxWaylandSupport.test.js`

- [ ] **Step 1: 跑 Node 全量**

Run: `node --test`
Expected: PASS

- [ ] **Step 2: 跑 Rust monitor 测试**

Run: `cargo test --manifest-path src-tauri/Cargo.toml monitor::tests`
Expected: PASS

- [ ] **Step 3: 跑 Rust screenshot 测试**

Run: `cargo test --manifest-path src-tauri/Cargo.toml screenshot::tests`
Expected: PASS

- [ ] **Step 4: 记录能力边界**

最终说明里必须写：

- KDE provider 依赖 `kdotool`
- Sway provider 依赖 `swaymsg`
- Hyprland provider 依赖 `hyprctl`
- Chromium 系 URL 仍属于最佳努力恢复，不等同于 macOS 那种强能力采集
