#![cfg_attr(not(target_os = "linux"), allow(dead_code))]

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LinuxDesktopSession {
    X11,
    Wayland,
    Unknown,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LinuxDesktopEnvironment {
    Gnome,
    Kde,
    Sway,
    Hyprland,
    Unknown,
}

impl LinuxDesktopSession {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::X11 => "x11",
            Self::Wayland => "wayland",
            Self::Unknown => "unknown",
        }
    }

    pub fn supports_active_window_tracking(self) -> bool {
        matches!(self, Self::X11)
    }

    pub fn supports_screenshot_capture(self) -> bool {
        matches!(self, Self::X11 | Self::Wayland)
    }
}

impl LinuxDesktopEnvironment {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Gnome => "gnome",
            Self::Kde => "kde",
            Self::Sway => "sway",
            Self::Hyprland => "hyprland",
            Self::Unknown => "unknown",
        }
    }
}

fn detect_linux_desktop_environment(
    xdg_current_desktop: Option<&str>,
    desktop_session: Option<&str>,
) -> LinuxDesktopEnvironment {
    let current_desktop = xdg_current_desktop
        .unwrap_or_default()
        .trim()
        .to_lowercase();
    let desktop_session = desktop_session.unwrap_or_default().trim().to_lowercase();

    let detect = |value: &str| -> Option<LinuxDesktopEnvironment> {
        if value.contains("gnome") {
            Some(LinuxDesktopEnvironment::Gnome)
        } else if value.contains("kde") || value.contains("plasma") {
            Some(LinuxDesktopEnvironment::Kde)
        } else if value.contains("sway") {
            Some(LinuxDesktopEnvironment::Sway)
        } else if value.contains("hyprland") || value.contains("hypr") {
            Some(LinuxDesktopEnvironment::Hyprland)
        } else {
            None
        }
    };

    detect(&current_desktop)
        .or_else(|| detect(&desktop_session))
        .unwrap_or(LinuxDesktopEnvironment::Unknown)
}

#[cfg(target_os = "linux")]
pub fn current_linux_desktop_session() -> LinuxDesktopSession {
    let session_type = std::env::var("XDG_SESSION_TYPE")
        .unwrap_or_default()
        .trim()
        .to_lowercase();

    match session_type.as_str() {
        "wayland" => return LinuxDesktopSession::Wayland,
        "x11" => return LinuxDesktopSession::X11,
        _ => {}
    }

    let wayland_display = std::env::var("WAYLAND_DISPLAY").unwrap_or_default();
    if !wayland_display.trim().is_empty() {
        return LinuxDesktopSession::Wayland;
    }

    let x11_display = std::env::var("DISPLAY").unwrap_or_default();
    if !x11_display.trim().is_empty() {
        return LinuxDesktopSession::X11;
    }

    LinuxDesktopSession::Unknown
}

#[cfg(not(target_os = "linux"))]
pub fn current_linux_desktop_session() -> LinuxDesktopSession {
    LinuxDesktopSession::Unknown
}

#[cfg(target_os = "linux")]
pub fn current_linux_desktop_environment() -> LinuxDesktopEnvironment {
    detect_linux_desktop_environment(
        std::env::var("XDG_CURRENT_DESKTOP").ok().as_deref(),
        std::env::var("DESKTOP_SESSION").ok().as_deref(),
    )
}

#[cfg(not(target_os = "linux"))]
pub fn current_linux_desktop_environment() -> LinuxDesktopEnvironment {
    LinuxDesktopEnvironment::Unknown
}

#[cfg(test)]
mod tests {
    use super::{
        detect_linux_desktop_environment, LinuxDesktopEnvironment, LinuxDesktopSession,
    };

    #[test]
    fn xdg_current_desktop应优先识别_gnome() {
        let detected =
            detect_linux_desktop_environment(Some("ubuntu:GNOME"), Some("plasma"));
        assert_eq!(detected, LinuxDesktopEnvironment::Gnome);
    }

    #[test]
    fn desktop_session应兜底识别_sway() {
        let detected = detect_linux_desktop_environment(None, Some("sway"));
        assert_eq!(detected, LinuxDesktopEnvironment::Sway);
    }

    #[test]
    fn 未命中桌面环境时应回退_unknown() {
        let detected =
            detect_linux_desktop_environment(Some(""), Some("custom-session"));
        assert_eq!(detected, LinuxDesktopEnvironment::Unknown);
    }

    #[test]
    fn x11会话仍应支持活动窗口追踪() {
        assert!(LinuxDesktopSession::X11.supports_active_window_tracking());
        assert!(!LinuxDesktopSession::Wayland.supports_active_window_tracking());
    }
}
