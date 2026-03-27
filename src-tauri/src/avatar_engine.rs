use serde::{Deserialize, Serialize};
use tauri::{
    AppHandle, Emitter, LogicalSize, Manager, Monitor, PhysicalPosition, Position, Size,
    WebviewUrl, WebviewWindow, WebviewWindowBuilder,
};

pub const AVATAR_WINDOW_LABEL: &str = "avatar";
pub const AVATAR_STATE_EVENT: &str = "avatar-state-changed";
pub const AVATAR_BUBBLE_EVENT: &str = "avatar-bubble";

const AVATAR_SCALE_MIN: f64 = 0.7;
const AVATAR_SCALE_MAX: f64 = 1.3;
const AVATAR_SCALE_DEFAULT: f64 = 0.9;
const AVATAR_OPACITY_DEFAULT: f64 = 0.82;
const AVATAR_WINDOW_BASE_WIDTH: f64 = 152.0;
const AVATAR_WINDOW_BASE_HEIGHT: f64 = 170.0;
const AVATAR_WINDOW_WIDTH: f64 = AVATAR_WINDOW_BASE_WIDTH * AVATAR_SCALE_DEFAULT;
const AVATAR_WINDOW_HEIGHT: f64 = AVATAR_WINDOW_BASE_HEIGHT * AVATAR_SCALE_DEFAULT;
const AVATAR_WINDOW_MARGIN: f64 = 8.0;

#[derive(Debug, Clone, Copy, PartialEq)]
struct Rect {
    x: i32,
    y: i32,
    width: i32,
    height: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct AvatarStatePayload {
    pub mode: String,
    pub app_name: String,
    pub context_label: String,
    pub hint: String,
    pub is_idle: bool,
    pub is_generating_report: bool,
    pub avatar_opacity: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct AvatarBubblePayload {
    pub message: String,
    pub tone: String,
}

impl AvatarBubblePayload {
    pub fn info(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            tone: "info".to_string(),
        }
    }

    pub fn success(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            tone: "success".to_string(),
        }
    }
}

pub fn default_avatar_state() -> AvatarStatePayload {
    AvatarStatePayload {
        mode: "idle".to_string(),
        app_name: "Work Review".to_string(),
        context_label: "待命中".to_string(),
        hint: "准备陪你开始工作".to_string(),
        is_idle: true,
        is_generating_report: false,
        avatar_opacity: AVATAR_OPACITY_DEFAULT,
    }
}

pub fn derive_avatar_state(
    app_name: &str,
    window_title: &str,
    is_idle: bool,
    is_generating_report: bool,
) -> AvatarStatePayload {
    let app_name = normalize_app_name(app_name);
    let category = crate::monitor::categorize_app(&app_name, window_title);

    if is_generating_report {
        return AvatarStatePayload {
            mode: "generating".to_string(),
            app_name,
            context_label: "生成中".to_string(),
            hint: "正在帮你整理今天的内容".to_string(),
            is_idle,
            is_generating_report: true,
            avatar_opacity: AVATAR_OPACITY_DEFAULT,
        };
    }

    if is_idle {
        return AvatarStatePayload {
            mode: "idle".to_string(),
            app_name,
            context_label: "待机中".to_string(),
            hint: "先歇一会，恢复状态再继续".to_string(),
            is_idle: true,
            is_generating_report: false,
            avatar_opacity: AVATAR_OPACITY_DEFAULT,
        };
    }

    if is_meeting_context(app_name.as_str(), window_title, &category) {
        AvatarStatePayload {
            mode: "meeting".to_string(),
            app_name,
            context_label: "开会中".to_string(),
            hint: "先把沟通结论收拢，再继续推进。".to_string(),
            is_idle: false,
            is_generating_report: false,
            avatar_opacity: AVATAR_OPACITY_DEFAULT,
        }
    } else if is_music_context(app_name.as_str(), window_title, &category) {
        AvatarStatePayload {
            mode: "music".to_string(),
            app_name,
            context_label: "听歌中".to_string(),
            hint: "保持节奏，但别让注意力被带跑。".to_string(),
            is_idle: false,
            is_generating_report: false,
            avatar_opacity: AVATAR_OPACITY_DEFAULT,
        }
    } else if is_video_context(app_name.as_str(), window_title, &category) {
        AvatarStatePayload {
            mode: "video".to_string(),
            app_name,
            context_label: "视频中".to_string(),
            hint: "先看完这一段，再决定下一步。".to_string(),
            is_idle: false,
            is_generating_report: false,
            avatar_opacity: AVATAR_OPACITY_DEFAULT,
        }
    } else if is_reading_context(app_name.as_str(), window_title, &category) {
        AvatarStatePayload {
            mode: "reading".to_string(),
            app_name,
            context_label: "阅读中".to_string(),
            hint: "正在吸收内容，先别打断节奏".to_string(),
            is_idle: false,
            is_generating_report: false,
            avatar_opacity: AVATAR_OPACITY_DEFAULT,
        }
    } else if is_slacking_context(app_name.as_str(), window_title, &category) {
        AvatarStatePayload {
            mode: "slacking".to_string(),
            app_name,
            context_label: "摸鱼中".to_string(),
            hint: "休息可以，但别忘了回来继续推进。".to_string(),
            is_idle: false,
            is_generating_report: false,
            avatar_opacity: AVATAR_OPACITY_DEFAULT,
        }
    } else {
        AvatarStatePayload {
            mode: "working".to_string(),
            app_name: app_name.clone(),
            context_label: "办公中".to_string(),
            hint: "保持推进，先把这一段收住".to_string(),
            is_idle: false,
            is_generating_report: false,
            avatar_opacity: AVATAR_OPACITY_DEFAULT,
        }
    }
}

pub fn apply_avatar_opacity(
    mut payload: AvatarStatePayload,
    opacity: f64,
) -> AvatarStatePayload {
    payload.avatar_opacity = opacity;
    payload
}

pub fn sync_avatar_window(app: &AppHandle, enabled: bool, scale: f64) -> tauri::Result<()> {
    if enabled {
        ensure_avatar_window(app, scale)?;
        if let Some(window) = app.get_webview_window(AVATAR_WINDOW_LABEL) {
            let normalized_scale = normalize_avatar_scale(scale);
            let (x, y) = default_avatar_position(app, normalized_scale);
            resize_avatar_window(&window, normalized_scale);
            let _ = window.set_always_on_top(true);
            let _ = window.set_visible_on_all_workspaces(true);
            let _ = window.set_skip_taskbar(true);
            let _ = window.set_position(Position::Physical(PhysicalPosition::new(x, y)));
            let _ = window.unminimize();
            let _ = window.show();
        }
    } else if let Some(window) = app.get_webview_window(AVATAR_WINDOW_LABEL) {
        let _ = window.hide();
    }

    Ok(())
}

pub fn emit_avatar_state(app: &AppHandle, payload: &AvatarStatePayload) {
    if let Some(window) = app.get_webview_window(AVATAR_WINDOW_LABEL) {
        let _ = window.emit(AVATAR_STATE_EVENT, payload);
    }
}

pub fn emit_avatar_bubble(app: &AppHandle, payload: &AvatarBubblePayload) {
    if let Some(window) = app.get_webview_window(AVATAR_WINDOW_LABEL) {
        let _ = window.emit(AVATAR_BUBBLE_EVENT, payload);
    }
}

fn ensure_avatar_window(app: &AppHandle, scale: f64) -> tauri::Result<()> {
    if app.get_webview_window(AVATAR_WINDOW_LABEL).is_some() {
        return Ok(());
    }

    let (window_width, window_height) = avatar_window_size(scale);

    let window = WebviewWindowBuilder::new(app, AVATAR_WINDOW_LABEL, WebviewUrl::default())
        .title("Work Review Avatar")
        .inner_size(window_width, window_height)
        .min_inner_size(window_width, window_height)
        .max_inner_size(window_width, window_height)
        .position(40.0, 40.0)
        .resizable(false)
        .maximizable(false)
        .minimizable(false)
        .closable(false)
        .decorations(false)
        .transparent(true)
        .visible(false)
        .always_on_top(true)
        .visible_on_all_workspaces(true)
        .skip_taskbar(true)
        .shadow(false)
        .focused(false)
        .build()?;

    let _ = window.set_always_on_top(true);
    let _ = window.set_visible_on_all_workspaces(true);
    let _ = window.set_skip_taskbar(true);

    Ok(())
}

fn resize_avatar_window(window: &WebviewWindow, scale: f64) {
    let (window_width, window_height) = avatar_window_size(scale);
    let _ = window.set_size(Size::Logical(LogicalSize::new(window_width, window_height)));
    let _ = window.set_min_size(Some(Size::Logical(LogicalSize::new(
        window_width,
        window_height,
    ))));
    let _ = window.set_max_size(Some(Size::Logical(LogicalSize::new(
        window_width,
        window_height,
    ))));
}

fn default_avatar_position(app: &AppHandle, scale: f64) -> (i32, i32) {
    if let Some(main_window) = app.get_webview_window("main") {
        if let Ok(Some(monitor)) = main_window.current_monitor() {
            let anchor = match (main_window.outer_position(), main_window.outer_size()) {
                (Ok(position), Ok(size)) => Some(Rect {
                    x: position.x,
                    y: position.y,
                    width: size.width as i32,
                    height: size.height as i32,
                }),
                _ => None,
            };

            return compute_avatar_position(monitor, anchor, scale);
        }
    }

    if let Ok(Some(monitor)) = app.primary_monitor() {
        return compute_avatar_position(monitor, None, scale);
    }

    (40, 40)
}

fn compute_avatar_position(monitor: Monitor, anchor: Option<Rect>, scale: f64) -> (i32, i32) {
    let (window_width, window_height) = avatar_window_size(scale);
    let work_area = monitor.work_area();
    let bounds = Rect {
        x: work_area.position.x,
        y: work_area.position.y,
        width: work_area.size.width as i32,
        height: work_area.size.height as i32,
    };

    let preferred_x = anchor
        .map(|rect| rect.x + rect.width - window_width as i32 - AVATAR_WINDOW_MARGIN as i32)
        .unwrap_or(bounds.x + bounds.width - window_width as i32 - AVATAR_WINDOW_MARGIN as i32);
    let preferred_y = anchor
        .map(|rect| rect.y + rect.height - window_height as i32 - AVATAR_WINDOW_MARGIN as i32)
        .unwrap_or(bounds.y + bounds.height - window_height as i32 - AVATAR_WINDOW_MARGIN as i32);

    clamp_avatar_position_with_size(bounds, preferred_x, preferred_y, window_width, window_height)
}

fn clamp_avatar_position(bounds: Rect, preferred_x: i32, preferred_y: i32) -> (i32, i32) {
    clamp_avatar_position_with_size(
        bounds,
        preferred_x,
        preferred_y,
        AVATAR_WINDOW_WIDTH,
        AVATAR_WINDOW_HEIGHT,
    )
}

fn clamp_avatar_position_with_size(
    bounds: Rect,
    preferred_x: i32,
    preferred_y: i32,
    window_width: f64,
    window_height: f64,
) -> (i32, i32) {
    let max_x = (bounds.x + bounds.width - window_width as i32).max(bounds.x);
    let max_y = (bounds.y + bounds.height - window_height as i32).max(bounds.y);

    (
        preferred_x.clamp(bounds.x, max_x),
        preferred_y.clamp(bounds.y, max_y),
    )
}

fn avatar_window_size(scale: f64) -> (f64, f64) {
    let normalized_scale = normalize_avatar_scale(scale);
    (
        ((AVATAR_WINDOW_BASE_WIDTH * normalized_scale) * 10.0).round() / 10.0,
        ((AVATAR_WINDOW_BASE_HEIGHT * normalized_scale) * 10.0).round() / 10.0,
    )
}

fn normalize_avatar_scale(scale: f64) -> f64 {
    if !scale.is_finite() {
        return AVATAR_SCALE_DEFAULT;
    }

    scale.clamp(AVATAR_SCALE_MIN, AVATAR_SCALE_MAX)
}

fn normalize_app_name(app_name: &str) -> String {
    let trimmed = app_name.trim();
    if trimmed.is_empty() || trimmed.eq_ignore_ascii_case("unknown") {
        "当前任务".to_string()
    } else {
        trimmed.to_string()
    }
}

fn contains_any(text: &str, keywords: &[&str]) -> bool {
    keywords.iter().any(|keyword| text.contains(keyword))
}

fn is_meeting_context(app_name: &str, window_title: &str, category: &str) -> bool {
    let app_lower = app_name.to_lowercase();
    let title_lower = window_title.to_lowercase();

    category == "communication"
        || contains_any(
            &app_lower,
            &["zoom", "teams", "meeting", "meet", "腾讯会议", "飞书会议", "dingtalk"],
        )
        || contains_any(
            &title_lower,
            &["会议", "例会", "meeting", "meet", "call", "huddle", "standup"],
        )
}

fn is_music_context(app_name: &str, window_title: &str, category: &str) -> bool {
    let app_lower = app_name.to_lowercase();
    let title_lower = window_title.to_lowercase();

    category == "entertainment"
        && (contains_any(
            &app_lower,
            &["spotify", "music", "网易云", "qqmusic", "apple music"],
        ) || contains_any(&title_lower, &["playlist", "album", "歌单", "音乐", "歌词"]))
}

fn is_video_context(app_name: &str, window_title: &str, category: &str) -> bool {
    let app_lower = app_name.to_lowercase();
    let title_lower = window_title.to_lowercase();

    contains_any(
        &app_lower,
        &["youtube", "netflix", "bilibili", "爱奇艺", "优酷", "腾讯视频", "vlc", "iina"],
    ) || (category == "entertainment"
        && contains_any(&title_lower, &["视频", "movie", "episode", "直播", "回放", "播放"]))
}

fn is_reading_context(app_name: &str, window_title: &str, category: &str) -> bool {
    let app_lower = app_name.to_lowercase();
    let title_lower = window_title.to_lowercase();

    contains_any(
        &app_lower,
        &["preview", "reader", "pdf", "kindle", "zotero", "notion", "obsidian", "typora"],
    )
        || (category == "browser"
            && contains_any(
                &title_lower,
                &["文档", "readme", "docs", "notion", "帮助", "manual", "guide", "wiki"],
            ))
        || app_lower.contains("preview")
        || app_lower.contains("reader")
        || app_lower.contains("pdf")
        || title_lower.contains("文档")
        || title_lower.contains("readme")
        || title_lower.contains("docs")
        || title_lower.contains("notion")
        || title_lower.contains("帮助")
}

fn is_slacking_context(app_name: &str, window_title: &str, category: &str) -> bool {
    let app_lower = app_name.to_lowercase();
    let title_lower = window_title.to_lowercase();

    (category == "entertainment"
        && !is_music_context(app_name, window_title, category)
        && !is_video_context(app_name, window_title, category))
        || contains_any(
            &app_lower,
            &["steam", "game", "微博", "小红书", "douyin", "抖音", "twitter", "x "],
        )
        || contains_any(
            &title_lower,
            &["微博", "小红书", "reddit", "douyin", "抖音", "游戏", "社区", "动态"],
        )
}

#[cfg(test)]
mod tests {
    use super::{
        avatar_window_size, clamp_avatar_position, default_avatar_state, derive_avatar_state, Rect,
        AVATAR_WINDOW_HEIGHT, AVATAR_WINDOW_WIDTH,
    };

    #[test]
    fn 空闲状态应优先进入待机模式() {
        let state = derive_avatar_state("VS Code", "main.rs", true, false);

        assert_eq!(state.mode, "idle");
        assert!(state.is_idle);
        assert_eq!(state.context_label, "待机中");
    }

    #[test]
    fn 日报生成应优先进入生成模式() {
        let state = derive_avatar_state("Google Chrome", "日报", false, true);

        assert_eq!(state.mode, "generating");
        assert!(state.is_generating_report);
        assert_eq!(state.context_label, "生成中");
    }

    #[test]
    fn 浏览器上下文应识别为阅读模式() {
        let state = derive_avatar_state("Google Chrome", "产品文档 - docs", false, false);

        assert_eq!(state.mode, "reading");
        assert_eq!(state.context_label, "阅读中");
    }

    #[test]
    fn 会议应用应识别为开会状态() {
        let state = derive_avatar_state("Zoom", "项目例会", false, false);

        assert_eq!(state.mode, "meeting");
        assert_eq!(state.context_label, "开会中");
    }

    #[test]
    fn 音乐应用应识别为音乐状态() {
        let state = derive_avatar_state("Spotify", "Daily Mix", false, false);

        assert_eq!(state.mode, "music");
        assert_eq!(state.context_label, "听歌中");
    }

    #[test]
    fn 视频应用应识别为视频状态() {
        let state = derive_avatar_state("Bilibili", "RustConf 回放", false, false);

        assert_eq!(state.mode, "video");
        assert_eq!(state.context_label, "视频中");
    }

    #[test]
    fn 娱乐场景应识别为摸鱼状态() {
        let state = derive_avatar_state("Steam", "Balatro", false, false);

        assert_eq!(state.mode, "slacking");
        assert_eq!(state.context_label, "摸鱼中");
    }

    #[test]
    fn 非阅读上下文应识别为工作模式() {
        let state = derive_avatar_state("Cursor", "commands.rs", false, false);

        assert_eq!(state.mode, "working");
        assert_eq!(state.context_label, "办公中");
    }

    #[test]
    fn 默认状态应可直接用于初始化() {
        let state = default_avatar_state();

        assert_eq!(state.mode, "idle");
        assert_eq!(state.app_name, "Work Review");
        assert!(!state.is_generating_report);
    }

    #[test]
    fn 桌宠窗口尺寸应随缩放变化() {
        let (small_w, small_h) = avatar_window_size(0.7);
        let (default_w, default_h) = avatar_window_size(0.9);
        let (large_w, large_h) = avatar_window_size(1.3);

        assert!(small_w < default_w);
        assert!(small_h < default_h);
        assert!(large_w > default_w);
        assert!(large_h > default_h);
        assert_eq!((default_w, default_h), (136.8, 153.0));
    }

    #[test]
    fn 桌宠位置应优先吸附到锚点右下侧() {
        let bounds = Rect {
            x: 0,
            y: 0,
            width: 1440,
            height: 900,
        };

        let (x, y) = clamp_avatar_position(bounds, 716, 356);

        assert_eq!((x, y), (716, 356));
    }

    #[test]
    fn 桌宠位置超出屏幕时应被钳制回可视区域() {
        let bounds = Rect {
            x: 0,
            y: 0,
            width: 1280,
            height: 720,
        };

        let (x, y) = clamp_avatar_position(bounds, 1200, 600);

        assert_eq!(
            (x, y),
            (
                1280 - AVATAR_WINDOW_WIDTH as i32,
                720 - AVATAR_WINDOW_HEIGHT as i32
            )
        );
    }
}
