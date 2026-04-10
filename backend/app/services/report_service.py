from datetime import datetime
from pathlib import Path

from .config_service import ensure_parent, load_config
from .data_service import get_hourly_summaries, get_report, get_timeline, get_today_stats


def _format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds or 0))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}小时")
    if minutes:
        parts.append(f"{minutes}分钟")
    if seconds or not parts:
        parts.append(f"{seconds}秒")
    return "".join(parts)


def _top_items(items: list[dict], key: str, limit: int = 10) -> list[dict]:
    return sorted(items, key=lambda item: item.get(key, 0), reverse=True)[:limit]


def _normalize_locale(locale: str | None) -> str:
    normalized = (locale or '').strip()
    return normalized or 'zh-CN'


def _report_labels(locale: str) -> dict[str, str]:
    if locale.startswith('en'):
        return {
            'title': 'Work Report',
            'date': 'Date',
            'overview': 'Overall Summary',
            'metric': 'Metric',
            'value': 'Value',
            'total_duration': 'Total work duration',
            'screenshots': 'Screenshots',
            'apps': 'Apps used',
            'sites': 'Visited websites',
            'categories': 'Top categories',
            'category': 'Category',
            'top_apps': 'Top applications',
            'rank': 'Rank',
            'app': 'Application',
            'websites': 'Website visits',
            'domain': 'Domain',
            'hourly': 'Hourly summaries',
            'notes': 'Generation notes',
            'mode': 'Generation mode',
            'prompt': 'Custom prompt',
            'configured': 'Configured',
            'not_configured': 'Not configured',
            'no_data': 'No data',
            'no_hourly': '- No hourly summaries',
        }
    if locale.startswith('zh-TW'):
        return {
            'title': '工作日報',
            'date': '日期',
            'overview': '整體概覽',
            'metric': '指標',
            'value': '數值',
            'total_duration': '總工作時長',
            'screenshots': '截圖數量',
            'apps': '使用應用數',
            'sites': '訪問網站數',
            'categories': '主要分類',
            'category': '分類',
            'top_apps': '主要應用',
            'rank': '排名',
            'app': '應用',
            'websites': '網站訪問',
            'domain': '域名',
            'hourly': '小時摘要',
            'notes': '生成說明',
            'mode': '生成模式',
            'prompt': '自定義提示詞',
            'configured': '已配置',
            'not_configured': '未配置',
            'no_data': '暫無數據',
            'no_hourly': '- 暫無小時摘要',
        }
    return {
        'title': '工作日报',
        'date': '日期',
        'overview': '整体概览',
        'metric': '指标',
        'value': '数值',
        'total_duration': '总工作时长',
        'screenshots': '截图数量',
        'apps': '使用应用数',
        'sites': '访问网站数',
        'categories': '主要分类',
        'category': '分类',
        'top_apps': '主要应用',
        'rank': '排名',
        'app': '应用',
        'websites': '网站访问',
        'domain': '域名',
        'hourly': '小时摘要',
        'notes': '生成说明',
        'mode': '生成模式',
        'prompt': '自定义提示词',
        'configured': '已配置',
        'not_configured': '未配置',
        'no_data': '暂无数据',
        'no_hourly': '- 暂无小时摘要',
    }


def build_report_content(date: str, locale: str | None = None) -> str:
    normalized_locale = _normalize_locale(locale)
    labels = _report_labels(normalized_locale)
    stats = get_today_stats() if date == datetime.now().strftime("%Y-%m-%d") else None
    timeline = get_timeline(date, limit=2000, offset=0)
    summaries = get_hourly_summaries(date)

    if stats is None:
        total_duration = sum(int(item.get("duration") or 0) for item in timeline)
        app_usage_map: dict[tuple[str, str | None], int] = {}
        category_usage_map: dict[str, int] = {}
        domain_usage_map: dict[str, int] = {}

        for item in timeline:
            app_key = (item.get("app_name") or labels['no_data'], item.get("executable_path"))
            app_usage_map[app_key] = app_usage_map.get(app_key, 0) + int(item.get("duration") or 0)

            category = item.get("category") or "other"
            category_usage_map[category] = category_usage_map.get(category, 0) + int(item.get("duration") or 0)

            browser_url = item.get("browser_url") or ""
            if browser_url:
                domain = browser_url.split("//")[-1].split("/")[0].split(":")[0]
                domain_usage_map[domain] = domain_usage_map.get(domain, 0) + int(item.get("duration") or 0)

        stats = {
            "date": date,
            "total_duration": total_duration,
            "screenshot_count": len(timeline),
            "work_time_duration": total_duration,
            "app_usage": [
                {"app_name": app_name, "duration": duration, "executable_path": executable_path}
                for (app_name, executable_path), duration in app_usage_map.items()
            ],
            "category_usage": [
                {"category": category, "duration": duration}
                for category, duration in category_usage_map.items()
            ],
            "domain_usage": [
                {"domain": domain, "duration": duration}
                for domain, duration in domain_usage_map.items()
            ],
        }

    top_apps = _top_items(stats.get("app_usage", []), "duration", 12)
    top_categories = _top_items(stats.get("category_usage", []), "duration", 8)
    top_domains = _top_items(stats.get("domain_usage", []), "duration", 8)

    lines = [
        f"# {labels['title']}",
        "",
        f"**{labels['date']}：{date}**",
        "",
        f"## 1. {labels['overview']}",
        "",
        f"| {labels['metric']} | {labels['value']} |",
        "|:--|--:|",
        f"| {labels['total_duration']} | {_format_duration(stats.get('total_duration', 0))} |",
        f"| {labels['screenshots']} | {int(stats.get('screenshot_count', 0))} |",
        f"| {labels['apps']} | {len(stats.get('app_usage', []))} |",
        f"| {labels['sites']} | {len(stats.get('domain_usage', []))} |",
        "",
        f"## 2. {labels['categories']}",
        "",
        f"| {labels['category']} | {labels['value']} |",
        "|:--|--:|",
    ]

    if top_categories:
        for item in top_categories:
            lines.append(f"| {item.get('category') or 'other'} | {_format_duration(item.get('duration', 0))} |")
    else:
        lines.append(f"| {labels['no_data']} | 0秒 |")

    lines.extend([
        "",
        f"## 3. {labels['top_apps']}",
        "",
        f"| {labels['rank']} | {labels['app']} | {labels['value']} |",
        "|--:|:--|--:|",
    ])

    if top_apps:
        for index, item in enumerate(top_apps, start=1):
            lines.append(f"| {index} | {item.get('app_name') or labels['no_data']} | {_format_duration(item.get('duration', 0))} |")
    else:
        lines.append(f"| 1 | {labels['no_data']} | 0秒 |")

    lines.extend([
        "",
        f"## 4. {labels['websites']}",
        "",
        f"| {labels['rank']} | {labels['domain']} | {labels['value']} |",
        "|--:|:--|--:|",
    ])

    if top_domains:
        for index, item in enumerate(top_domains, start=1):
            lines.append(f"| {index} | {item.get('domain') or labels['no_data']} | {_format_duration(item.get('duration', 0))} |")
    else:
        lines.append(f"| 1 | {labels['no_data']} | 0秒 |")

    lines.extend([
        "",
        f"## 5. {labels['hourly']}",
        "",
    ])

    if summaries:
        for summary in summaries[:12]:
            lines.append(
                f"- {int(summary.get('hour', 0)):02d}:00 - {_format_duration(summary.get('total_duration', 0))}：{summary.get('summary') or labels['no_data']}"
            )
    else:
        lines.append(labels['no_hourly'])

    config = load_config()
    lines.extend([
        "",
        f"## 6. {labels['notes']}",
        "",
        f"- {labels['mode']}：{config.get('ai_mode') or 'local'}",
        f"- {labels['prompt']}：{labels['configured'] if (config.get('daily_report_custom_prompt') or '').strip() else labels['not_configured']}",
        f"- Locale：{normalized_locale}",
        "",
    ])

    return "\n".join(lines)


def export_report_markdown(date: str, content: str, export_dir: str, locale: str | None = None) -> str:
    target_dir = Path((export_dir or '').strip()).expanduser()
    if not str(target_dir).strip():
        raise ValueError('导出目录不能为空')

    normalized_locale = _normalize_locale(locale).replace('/', '-').replace('\\', '-')
    ensure_parent(target_dir / 'placeholder.txt')
    file_path = target_dir / f"work-report-{date}-{normalized_locale}.md"
    file_path.write_text(content or '', encoding='utf-8')
    return str(file_path)


def generate_report_for_date(date: str, force: bool = True, locale: str | None = None) -> dict:
    normalized_locale = _normalize_locale(locale)
    existing = get_report(date, normalized_locale)
    if existing and not force and existing.get('locale') == normalized_locale:
        return existing

    # 先自动生成小时摘要
    try:
        from .hourly_service import generate_hourly_summaries
        generate_hourly_summaries(date)
    except Exception:
        pass

    content = build_report_content(date, normalized_locale)
    config = load_config()
    ai_mode = config.get('ai_mode') or 'local'
    model_name = None

    # AI 增强模式
    if ai_mode == 'summary':
        try:
            from .ai_service import generate_ai_report
            custom_prompt = config.get('daily_report_custom_prompt') or ''
            ai_result = generate_ai_report(date, content, custom_prompt, normalized_locale)
            if ai_result.get('content'):
                content = ai_result['content']
            model_name = ai_result.get('model')
        except Exception:
            pass  # AI 不可用时回退到模板

    report = {
        'date': date,
        'locale': normalized_locale,
        'content': content,
        'ai_mode': ai_mode,
        'model_name': model_name,
        'created_at': int(datetime.now().timestamp()),
    }

    from .report_store_service import save_report
    save_report(report)
    return report
