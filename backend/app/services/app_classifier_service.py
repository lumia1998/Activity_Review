"""应用自动分类服务 - 根据应用名/窗口标题/可执行路径自动分类"""
from __future__ import annotations

from typing import Any

# 应用分类规则（按优先级匹配）
# 格式: (patterns: list[str], category: str)
_APP_RULES: list[tuple[list[str], str]] = [
    # 开发工具
    ([
        'code', 'vscode', 'cursor', 'pycharm', 'intellij', 'webstorm', 'xcode',
        'android studio', 'idea', 'eclipse', 'netbeans', 'sublime', 'atom',
        'vim', 'nvim', 'neovim', 'emacs', 'zed', 'fleet',
        'terminal', 'iterm', 'warp', 'alacritty', 'kitty', 'hyper',
        'cmd', 'powershell', 'bash', 'zsh', 'git', 'mingw',
        'visual studio', 'devenv', 'rider', 'clion', 'goland', 'rustrover',
        'datagrip', 'dataspell', 'rubymine', 'phpstorm',
    ], 'development'),

    # 浏览器
    ([
        'chrome', 'firefox', 'safari', 'edge', 'opera', 'brave',
        'vivaldi', 'arc', 'tor browser', 'chromium',
        'firefox developer', 'firefox nightly',
    ], 'browser'),

    # 通讯工具
    ([
        '微信', 'wechat', 'qq', 'telegram', 'discord', 'slack',
        'teams', 'zoom', 'skype', '钉钉', 'dingtalk', '飞书', 'feishu', 'lark',
        '企业微信', 'wework', '腾讯会议', 'tencent meeting',
        'whatsapp', 'signal', 'line', 'messenger', 'enigma',
        'outlook', 'thunderbird', 'mail', 'foxmail',
    ], 'communication'),

    # 办公软件
    ([
        'word', 'excel', 'powerpoint', 'onenote', 'access', 'publisher',
        'wps', 'libreoffice', 'openoffice', 'pages', 'numbers', 'keynote',
        'notion', 'obsidian', 'logseq', 'roam', 'evernote', '印象笔记',
        'typora', 'marktext', 'notepad', 'notepad++',
        'confluence', 'yuque', '语雀', '飞书文档',
        'excel', 'spreadsheet', 'calc', 'sheet',
    ], 'office'),

    # 设计工具
    ([
        'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator',
        'indesign', 'after effects', 'premiere', 'blender', 'cinema 4d',
        'inkscape', 'gimp', 'canva', 'axure', '墨刀', 'pixso',
        'principle', 'framer', 'spline', 'rive',
    ], 'design'),

    # 娱乐
    ([
        'steam', 'epic games', 'origin', 'ubisoft', 'battle.net',
        'spotify', 'netease cloud music', '网易云音乐', 'qq music', 'qq音乐',
        'apple music', 'vlc', 'potplayer', 'mpv', 'iina',
        'bilibili', 'youtube', 'netflix', 'disney+',
        '游戏', 'game', 'minecraft', 'league', 'csgo',
    ], 'entertainment'),

    # AI 工具
    ([
        'chatgpt', 'openai', 'claude', 'deepseek', 'kimi', 'gemini',
        'copilot', 'midjourney', 'stable diffusion', 'dall-e',
        'poe', 'perplexity', 'tongyi', '通义', '文心', 'doubao', '豆包',
    ], 'ai_tools'),

    # 文件管理
    ([
        'finder', 'explorer', 'total commander', 'directory opus',
        'filezilla', 'transmit', 'cyberduck', 'winscp',
    ], 'file_management'),

    # 系统工具
    ([
        'activity monitor', 'task manager', 'system preferences',
        'settings', 'control panel', 'registry editor',
        'terminal', 'console', 'monitor', 'resource',
    ], 'system'),
]

# 浏览器可执行路径关键词
_BROWSER_EXECUTABLES = {
    'chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe', 'brave.exe',
    'vivaldi.exe', 'arc.exe', 'safari', 'chromium.exe',
}

# 已知浏览器应用名
_BROWSER_NAMES = {
    'google chrome', 'chrome', 'firefox', 'microsoft edge', 'edge',
    'opera', 'brave', 'safari', 'vivaldi', 'arc', 'chromium',
    'firefox developer edition', 'firefox nightly',
}


def classify_app(
    app_name: str | None,
    window_title: str | None = None,
    executable_path: str | None = None,
    config_rules: list[dict] | None = None,
) -> str:
    """自动分类应用

    Args:
        app_name: 应用名称
        window_title: 窗口标题
        executable_path: 可执行文件路径
        config_rules: 用户自定义规则

    Returns:
        分类名称
    """
    if not app_name:
        return 'other'

    # 优先检查用户自定义规则
    if config_rules:
        lower_app = app_name.strip().lower()
        for rule in config_rules:
            rule_app = (rule.get('app_name') or '').strip().lower()
            if rule_app and rule_app == lower_app:
                return rule.get('category') or 'other'

    lower_name = app_name.strip().lower()

    # 检查是否是浏览器（用于 URL 追踪）
    if _is_browser(app_name, executable_path):
        return 'browser'

    # 按规则匹配
    title_lower = (window_title or '').lower()
    corpus = f'{lower_name} {title_lower}'

    for patterns, category in _APP_RULES:
        # 跳过浏览器分类，已在上面处理
        if category == 'browser':
            continue
        for pattern in patterns:
            if pattern in corpus:
                return category

    # 根据可执行路径路径判断
    if executable_path:
        exe_lower = executable_path.lower().replace('\\', '/')
        for patterns, category in _APP_RULES:
            for pattern in patterns:
                if pattern in exe_lower:
                    return category

    return 'other'


def _is_browser(app_name: str | None, executable_path: str | None = None) -> bool:
    """判断应用是否是浏览器"""
    if not app_name:
        return False

    lower_name = app_name.strip().lower()
    if lower_name in _BROWSER_NAMES:
        return True

    if executable_path:
        exe_name = executable_path.replace('\\', '/').split('/')[-1].lower()
        if exe_name in _BROWSER_EXECUTABLES:
            return True

    return False


def get_app_category_overview() -> list[dict[str, Any]]:
    """获取所有应用分类概览

    Returns:
        分类规则列表
    """
    result = []
    for patterns, category in _APP_RULES:
        result.append({
            'category': category,
            'keywords': patterns[:5],  # 只显示前5个关键词
            'count': len(patterns),
        })
    return result


def reclassify_app_history(app_name: str, new_category: str) -> int:
    """重新分类指定应用的所有历史记录

    Args:
        app_name: 应用名称
        new_category: 新分类

    Returns:
        更新的记录数
    """
    from .data_service import get_connection, database_path, table_exists

    db_path = database_path()
    if not db_path.exists():
        return 0

    with get_connection() as connection:
        if not table_exists(connection, 'activities'):
            return 0

        normalized = app_name.strip().lower()
        cursor = connection.execute(
            'UPDATE activities SET category = ? WHERE LOWER(TRIM(app_name)) = ?',
            (new_category, normalized),
        )
        connection.commit()
        return int(cursor.rowcount or 0)
