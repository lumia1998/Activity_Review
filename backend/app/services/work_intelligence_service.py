"""工作智能服务 - 会话聚合、意图识别、周报生成、TODO提取

从旧版工作智能模块移植
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

SESSION_GAP_SECONDS = 15 * 60
DEEP_WORK_THRESHOLD_SECONDS = 45 * 60
TODO_TEXT_LIMIT = 80

# 意图分类关键词映射
INTENT_PATTERNS: dict[str, list[str]] = {
    '编码开发': [
        'cursor', 'vscode', 'visual studio code', 'code', 'pycharm', 'intellij',
        'xcode', 'webstorm', 'terminal', 'iterm', 'warp', 'git', 'commit',
        'branch', 'merge', 'cargo', 'npm', 'pnpm', 'debug', 'feature', '代码', '开发',
    ],
    '代码评审': [
        'pull request', 'merge request', 'code review', 'review', 'diff',
        'approval', 'comment', 'pr ', ' mr ', '评审', '审查',
    ],
    '需求文档': [
        'prd', 'spec', 'doc', 'docs', 'document', 'notion', '语雀', '飞书文档',
        'confluence', '需求', '文档', '方案', '设计稿',
    ],
    '会议沟通': [
        'zoom', 'meeting', 'meet', 'teams', 'slack', 'discord', '飞书',
        '企业微信', '会议', '沟通', '同步', '站会', '腾讯会议',
    ],
    '问题排查': [
        'bug', 'issue', 'error', 'exception', 'traceback', 'stack trace',
        'failed', 'failure', '日志', '报错', '修复', '排查', '异常',
    ],
    '测试验证': [
        'test', 'pytest', 'vitest', 'playwright', 'cypress', 'junit',
        'assert', '验证', '回归', '测试', '单测',
    ],
    '学习调研': [
        'google', 'stackoverflow', 'docs', 'documentation', 'guide',
        'tutorial', 'research', 'readme', '调研', '教程', '文档', '资料',
    ],
    'AI 协作': [
        'chatgpt', 'openai', 'claude', 'deepseek', 'kimi', 'gemini',
        'copilot', 'cursor', 'llm', 'prompt', '大模型',
    ],
    '项目管理': [
        'jira', 'linear', 'asana', 'trello', 'roadmap', 'milestone',
        'todoist', 'sprint', '任务', '排期', '看板', '项目',
    ],
}

# 正则表达式（延迟编译）
_CHECKBOX_RE = re.compile(r'(?m)\[[ xX]?\]\s*([^\n]{2,80})')
_EXPLICIT_TODO_RE = re.compile(
    r'(?i)(todo|待办|follow[- ]?up|next step|后续动作|需要跟进)\s*[:：-]?\s*([^\n。；]{2,80})'
)
_ACTION_TODO_RE = re.compile(
    r'(?i)(修复|排查|优化|补充|整理|确认|同步|review|fix|investigate|refactor|verify)\s*[:：-]?\s*([^\n。；]{0,60})'
)

# 噪声词
_NOISE_TOKENS = frozenset({
    'https', 'http', 'www', 'com', 'the', 'and', 'with', 'for', 'from',
    'into', 'main', 'work', 'review', '页面', '窗口', '文件', '今天', '进行', '正在',
})


def _format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds or 0))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts: list[str] = []
    if hours:
        parts.append(f'{hours}小时')
    if minutes:
        parts.append(f'{minutes}分钟')
    if seconds or not parts:
        parts.append(f'{seconds}秒')
    return ''.join(parts)


def _extract_domain(url: str | None) -> str:
    if not url:
        return ''
    url = url.strip()
    if '://' in url:
        url = url.split('://', 1)[1]
    domain = url.split('/', 1)[0].split(':')[0].lower()
    return domain


def _date_from_timestamp(timestamp: int) -> str:
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    except (OSError, ValueError):
        return ''


def _extract_keywords(text: str) -> list[str]:
    def _is_cjk(ch: str) -> bool:
        return '\u4e00' <= ch <= '\u9fff'

    tokens = re.split(r'[^\w]+', text)
    result = []
    for token in tokens:
        token = token.strip()
        if len(token) < 2:
            continue
        lowered = token.lower()
        if lowered in _NOISE_TOKENS:
            continue
        result.append(lowered)
    return result


def _truncate_text(value: str, max_chars: int = TODO_TEXT_LIMIT) -> str:
    value = value.strip()
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + '…'


def _clean_todo_text(value: str) -> str:
    return (
        value.replace('\n', ' ').replace('\r', ' ')
        .replace('[]', '').replace('[ ]', '').replace('[x]', '')
        .strip(':：- ')
        .strip()
    )


def _normalize_candidate(value: str) -> str:
    return ''.join(ch.lower() for ch in value if ch.isalnum() or '\u4e00' <= ch <= '\u9fff')


def _top_by_duration(mapping: dict[str, int]) -> str:
    if not mapping:
        return ''
    return max(mapping.items(), key=lambda item: (item[1], item[0]))[0]


def _top_by_count(mapping: dict[str, int]) -> str:
    if not mapping:
        return ''
    return max(mapping.items(), key=lambda item: (item[1], item[0]))[0]


def _top_named_durations(mapping: dict[str, int], limit: int) -> list[dict[str, Any]]:
    items = [{'name': name, 'duration': duration} for name, duration in mapping.items()]
    items.sort(key=lambda item: (-item['duration'], item['name']))
    return items[:limit]


def _top_keywords(keyword_counts: dict[str, int], limit: int) -> list[str]:
    items = sorted(keyword_counts.items(), key=lambda item: (-item[1], len(item[0]), item[0]))
    return [keyword for keyword, _ in items[:limit]]


def _score_intent(label: str, corpus: str, patterns: list[str], score_per_hit: int) -> dict[str, Any]:
    evidence: list[str] = []
    score = 0
    for pattern in patterns:
        if pattern in corpus:
            score += score_per_hit
            evidence.append(f'命中关键词 {pattern}')
    return {'label': label, 'score': score, 'evidence': evidence}


def _classify_session(
    dominant_category: str,
    dominant_app: str,
    title: str,
    browser_domains: list[str],
    top_keywords: list[str],
    combined_lines: list[str],
) -> dict[str, Any]:
    lower_app = dominant_app.lower()
    lower_title = title.lower()
    domain_text = ' '.join(browser_domains).lower()
    keyword_text = ' '.join(top_keywords).lower()
    corpus = ' '.join(combined_lines).lower()

    matches = []
    for label, patterns in INTENT_PATTERNS.items():
        score_per_hit = 12 if label in ('编码开发', '代码评审', '会议沟通', '问题排查') else (
            14 if label == '代码评审' else 10 if label in ('需求文档', '项目管理') else 9 if label == 'AI 协作' else 8
        )
        matches.append(_score_intent(label, corpus, patterns, score_per_hit))

    # 额外加分规则
    if dominant_category == 'development':
        _add_score(matches, '编码开发', 10, '主类别为 development')
    if 'browser' in lower_app or 'chrome' in lower_app or 'safari' in lower_app:
        _add_score(matches, '学习调研', 4, '会话主要发生在浏览器')
    if 'pr' in lower_title or 'review' in lower_title:
        _add_score(matches, '代码评审', 8, f'标题包含 {title}')
    if 'github.com' in domain_text:
        _add_score(matches, '编码开发', 6, '包含 github.com')
        _add_score(matches, '代码评审', 4, '包含 github.com')
    if 'openai.com' in domain_text or 'claude.ai' in domain_text or 'chat.deepseek.com' in domain_text:
        _add_score(matches, 'AI 协作', 10, '包含 AI 工具站点')
    if 'bug' in keyword_text or '报错' in keyword_text:
        _add_score(matches, '问题排查', 8, '关键词显示异常处理')

    matches.sort(key=lambda item: (-item['score'], item['label']))
    best = next((item for item in matches if item['score'] > 0), None)
    if best is None:
        best = {'label': '通用工作', 'score': 40, 'evidence': ['未命中明确意图信号，按通用工作处理']}

    return {
        'label': best['label'],
        'score': min(max(40 + best['score'] if best['score'] > 0 else 40, 35), 95),
        'evidence': best['evidence'][:4],
    }


def _add_score(matches: list[dict], label: str, delta: int, evidence: str) -> None:
    for item in matches:
        if item['label'] == label:
            item['score'] += delta
            item['evidence'].append(evidence)
            break


# ---- 数据结构 ----

class WorkSession:
    __slots__ = (
        'session_id', 'date', 'start_timestamp', 'end_timestamp', 'duration',
        'activity_count', 'app_count', 'dominant_app', 'dominant_category',
        'title', 'browser_domains', 'top_apps', 'top_keywords',
        'intent_label', 'intent_confidence', 'intent_evidence',
    )

    def __init__(self, **kwargs: Any) -> None:
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot))

    def to_dict(self) -> dict[str, Any]:
        return {
            'sessionId': self.session_id,
            'date': self.date,
            'startTimestamp': self.start_timestamp,
            'endTimestamp': self.end_timestamp,
            'duration': self.duration,
            'activityCount': self.activity_count,
            'appCount': self.app_count,
            'dominantApp': self.dominant_app,
            'dominantCategory': self.dominant_category,
            'title': self.title,
            'browserDomains': self.browser_domains,
            'topApps': self.top_apps,
            'topKeywords': self.top_keywords,
            'intentLabel': self.intent_label,
            'intentConfidence': self.intent_confidence,
            'intentEvidence': self.intent_evidence,
        }


class _SessionAccumulator:
    def __init__(self, activity: dict) -> None:
        self.activities: list[dict] = [activity]
        dur = max(int(activity.get('duration') or 0), 1)
        ts = int(activity.get('timestamp') or 0)
        self.start_timestamp = ts
        self.end_timestamp = ts + dur
        self.total_duration = dur

    def can_merge(self, next_activity: dict) -> bool:
        ts = int(next_activity.get('timestamp') or 0)
        return ts - self.end_timestamp <= SESSION_GAP_SECONDS

    def push(self, activity: dict) -> None:
        ts = int(activity.get('timestamp') or 0)
        dur = max(int(activity.get('duration') or 0), 1)
        self.end_timestamp = max(self.end_timestamp, ts + dur)
        self.total_duration += dur
        self.activities.append(activity)

    def finalize(self, index: int) -> WorkSession:
        app_durations: dict[str, int] = defaultdict(int)
        category_durations: dict[str, int] = defaultdict(int)
        domain_durations: dict[str, int] = defaultdict(int)
        keyword_counts: dict[str, int] = defaultdict(int)
        title_counts: dict[str, int] = defaultdict(int)
        combined_lines: list[str] = []

        for act in self.activities:
            app_name = act.get('app_name') or '未知应用'
            category = act.get('category') or 'other'
            duration = max(int(act.get('duration') or 0), 1)

            app_durations[app_name] += duration
            category_durations[category] += duration

            window_title = (act.get('window_title') or '').strip()
            if window_title:
                title_counts[window_title] += 1

            browser_url = act.get('browser_url') or ''
            domain = _extract_domain(browser_url)
            if domain:
                domain_durations[domain] += duration

            ocr_text = act.get('ocr_text') or ''
            parts = [app_name, window_title, ocr_text, browser_url]
            joined = ' '.join(p for p in parts if p)
            combined_lines.append(joined)
            for token in _extract_keywords(joined):
                keyword_counts[token] += 1

        dominant_app = _top_by_duration(dict(app_durations)) or '未知应用'
        dominant_category = _top_by_duration(dict(category_durations)) or 'unknown'
        title = _top_by_count(dict(title_counts)) or dominant_app
        browser_domains_list = [item['name'] for item in _top_named_durations(dict(domain_durations), 4)]
        top_apps = _top_named_durations(dict(app_durations), 4)
        top_kw = _top_keywords(dict(keyword_counts), 6)

        intent = _classify_session(
            dominant_category, dominant_app, title,
            browser_domains_list, top_kw, combined_lines,
        )

        return WorkSession(
            session_id=f'{_date_from_timestamp(self.start_timestamp)}-{self.start_timestamp}-{index + 1}',
            date=_date_from_timestamp(self.start_timestamp),
            start_timestamp=self.start_timestamp,
            end_timestamp=self.end_timestamp,
            duration=max(self.total_duration, 1),
            activity_count=len(self.activities),
            app_count=len(app_durations),
            dominant_app=dominant_app,
            dominant_category=dominant_category,
            title=title,
            browser_domains=browser_domains_list,
            top_apps=top_apps,
            top_keywords=top_kw,
            intent_label=intent['label'],
            intent_confidence=intent['score'],
            intent_evidence=intent['evidence'],
        )


def build_work_sessions(activities: list[dict]) -> list[WorkSession]:
    """构建工作会话列表

    将活动按时间排序，15分钟间隔内的活动合并为同一会话。
    """
    sorted_activities = sorted(activities, key=lambda a: (int(a.get('timestamp') or 0), int(a.get('id') or 0)))

    sessions: list[WorkSession] = []
    current: _SessionAccumulator | None = None

    for activity in sorted_activities:
        if current is not None:
            if current.can_merge(activity):
                current.push(activity)
            else:
                sessions.append(current.finalize(len(sessions)))
                current = _SessionAccumulator(activity)
        else:
            current = _SessionAccumulator(activity)

    if current is not None:
        sessions.append(current.finalize(len(sessions)))

    sessions.sort(key=lambda s: -s.start_timestamp)
    return sessions


def analyze_intents(activities: list[dict]) -> dict[str, Any]:
    """分析工作意图

    Returns:
        {'sessions': [...], 'summary': [...]}
    """
    sessions = build_work_sessions(activities)
    summary_map: dict[str, list[int | int]] = {}

    for session in sessions:
        if session.intent_label not in summary_map:
            summary_map[session.intent_label] = [0, 0]
        summary_map[session.intent_label][0] += session.duration
        summary_map[session.intent_label][1] += 1

    summary = [
        {'label': label, 'duration': data[0], 'sessionCount': data[1]}
        for label, data in summary_map.items()
    ]
    summary.sort(key=lambda item: (-item['duration'], -item['sessionCount'], item['label']))

    return {
        'sessions': [s.to_dict() for s in sessions],
        'summary': summary,
    }


def generate_weekly_review(
    activities: list[dict],
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """生成周报

    Returns:
        WeeklyReviewResult
    """
    analysis = analyze_intents(activities)
    sessions = analysis['sessions']

    total_duration = sum(s.get('duration', 0) for s in sessions)
    session_count = len(sessions)
    deep_work_sessions = sum(1 for s in sessions if s.get('duration', 0) >= DEEP_WORK_THRESHOLD_SECONDS)

    day_durations: dict[str, int] = defaultdict(int)
    app_durations: dict[str, int] = defaultdict(int)
    context_switch_sessions = 0

    for session in sessions:
        day_durations[session.get('date', '')] += session.get('duration', 0)
        for app in (session.get('topApps') or []):
            app_durations[app['name']] += app['duration']
        if session.get('appCount', 0) >= 4:
            context_switch_sessions += 1

    active_days = len(day_durations)
    top_apps = _top_named_durations(dict(app_durations), 5)
    top_intents = analysis['summary'][:5]

    busiest_day = max(day_durations.items(), key=lambda item: (item[1], item[0])) if day_durations else None
    avg_session_duration = total_duration // session_count if session_count > 0 else 0

    # 高亮
    highlights: list[str] = []
    if top_intents:
        primary = top_intents[0]
        highlights.append(f'本阶段投入最多的是"{primary["label"]}"，累计 {_format_duration(primary["duration"])}。')
    if busiest_day:
        highlights.append(f'{busiest_day[0]} 是投入最高的一天，累计 {_format_duration(busiest_day[1])}。')
    if deep_work_sessions > 0:
        highlights.append(f'出现 {deep_work_sessions} 段超过 45 分钟的连续专注时段。')
    if not highlights:
        highlights.append('当前时间范围内记录较少，暂时无法形成稳定模式。')

    # 风险
    risks: list[str] = []
    if 0 < avg_session_duration < 20 * 60:
        risks.append('平均 session 偏短，任务切换可能较频繁。')
    if session_count > 0 and context_switch_sessions * 2 >= session_count:
        risks.append('多应用混合 session 偏多，建议留意上下文切换成本。')
    meeting_intent = next((item for item in top_intents if item['label'] == '会议沟通'), None)
    if meeting_intent and meeting_intent['duration'] * 4 >= max(total_duration, 1):
        risks.append('会议沟通占比较高，注意给深度工作预留整块时间。')
    if not risks:
        risks.append('整体节奏较稳定，没有明显异常信号。')

    title = f'工作复盘（{date_from or "最早记录"} ~ {date_to or "最近记录"}）'

    markdown_lines = [
        f'# {title}', '',
        '## 本期概览', '',
        f'- 总投入时长：{_format_duration(total_duration)}',
        f'- 活跃天数：{active_days} 天',
        f'- session 数量：{session_count} 段',
        f'- 深度工作段：{deep_work_sessions} 段', '',
        '## 重点工作', '',
    ]
    if not top_intents:
        markdown_lines.append('- 暂无足够数据识别重点工作。')
    else:
        for item in top_intents:
            markdown_lines.append(f'- {item["label"]}：{_format_duration(item["duration"])}，共 {item["sessionCount"]} 段')
    markdown_lines.append('')

    markdown_lines.extend(['## 核心观察', ''])
    for line in highlights:
        markdown_lines.append(f'- {line}')
    markdown_lines.append('')

    markdown_lines.extend(['## 风险与提醒', ''])
    for line in risks:
        markdown_lines.append(f'- {line}')
    markdown_lines.append('')

    markdown_lines.extend(['## 下阶段建议', ''])
    if 0 < avg_session_duration < 20 * 60:
        markdown_lines.append('- 给复杂任务预留 45 到 90 分钟的完整时间块，减少碎片切换。')
    else:
        markdown_lines.append('- 延续当前节奏，把高价值任务继续放到连续时间段里推进。')
    if top_apps:
        markdown_lines.append(f'- 继续围绕 {top_apps[0]["name"]} 这个主阵地沉淀产出，避免工具切换带来的分心。')

    return {
        'title': title,
        'markdown': '\n'.join(markdown_lines),
        'totalDuration': total_duration,
        'activeDays': active_days,
        'sessionCount': session_count,
        'deepWorkSessions': deep_work_sessions,
        'topIntents': top_intents,
        'topApps': top_apps,
        'highlights': highlights,
        'risks': risks,
    }


def extract_todos(activities: list[dict]) -> dict[str, Any]:
    """从活动记录中提取待办事项

    Returns:
        {'items': [...], 'summary': str}
    """
    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    for activity in activities:
        sources = _build_todo_sources(activity)
        for candidate, confidence, reason in sources:
            normalized = _normalize_candidate(candidate)
            if len(normalized) < 4 or normalized in seen:
                continue
            seen.add(normalized)

            ts = int(activity.get('timestamp') or 0)
            items.append({
                'title': candidate,
                'date': _date_from_timestamp(ts),
                'sourceTitle': _truncate_text(activity.get('window_title') or '', TODO_TEXT_LIMIT),
                'sourceApp': activity.get('app_name') or '',
                'confidence': confidence,
                'reason': reason,
            })

    items.sort(key=lambda item: (-item['confidence'], -item.get('date', '').count('-'), item['title']))
    items = items[:20]

    summary = (
        f'共提取到 {len(items)} 条候选待办，已按置信度排序。'
        if items else '当前时间范围内没有提取到明确的待办信号。'
    )

    return {'items': items, 'summary': summary}


def _build_todo_sources(activity: dict) -> list[tuple[str, int, str]]:
    candidates: list[tuple[str, int, str]] = []
    texts = [activity.get('window_title') or '']
    ocr_text = activity.get('ocr_text')
    if ocr_text:
        texts.append(ocr_text)
    browser_url = activity.get('browser_url')
    if browser_url:
        texts.append(browser_url)

    for text in texts:
        for match in _CHECKBOX_RE.finditer(text):
            candidates.append((_truncate_text(match.group(1)), 90, '命中未完成清单项'))

        for match in _EXPLICIT_TODO_RE.finditer(text):
            candidates.append((_truncate_text(_clean_todo_text(match.group(0))), 82, '命中显式待办关键词'))

        for match in _ACTION_TODO_RE.finditer(text):
            candidates.append((_truncate_text(_clean_todo_text(match.group(0))), 68, '命中动作型任务短语'))

    title_lower = (activity.get('window_title') or '').lower()
    if any(kw in title_lower for kw in ('issue', 'bug', 'pr #', '任务')):
        candidates.append((
            _truncate_text(activity.get('window_title') or '', TODO_TEXT_LIMIT),
            60, '窗口标题像是待跟进事项',
        ))

    return candidates
