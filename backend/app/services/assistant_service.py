from datetime import datetime
import time
from typing import Any
from urllib import error, request

from .data_service import get_hourly_summaries, get_report, get_timeline


def _format_duration(seconds: int | None) -> str:
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


def _score_text(query: str, text: str) -> int:
    score = 0
    lowered_query = query.lower()
    lowered_text = (text or '').lower()
    for token in [part for part in lowered_query.replace('？', ' ').replace('?', ' ').split() if part]:
        if token in lowered_text:
            score += max(1, len(token))
    return score


def search_memory(query: str, limit: int = 8) -> list[dict[str, Any]]:
    query = (query or '').strip()
    if not query:
        return []

    today = datetime.now().strftime('%Y-%m-%d')
    timeline = get_timeline(today, limit=300, offset=0)
    hourly = get_hourly_summaries(today)
    report = get_report(today)
    items: list[dict[str, Any]] = []

    for item in timeline:
        title = item.get('window_title') or item.get('app_name') or '活动记录'
        excerpt = item.get('ocr_text') or item.get('browser_url') or title
        score = _score_text(query, f"{title} {excerpt} {item.get('app_name') or ''}")
        if score <= 0:
            continue
        items.append({
            'sourceType': 'activity',
            'sourceId': item.get('id'),
            'date': today,
            'timestamp': item.get('timestamp') or 0,
            'title': title,
            'excerpt': excerpt,
            'appName': item.get('app_name'),
            'browserUrl': item.get('browser_url'),
            'duration': item.get('duration'),
            'score': score,
        })

    for summary in hourly:
        text = summary.get('summary') or ''
        score = _score_text(query, f"{text} {summary.get('main_apps') or ''}")
        if score <= 0:
            continue
        items.append({
            'sourceType': 'hourly_summary',
            'sourceId': None,
            'date': today,
            'timestamp': 0,
            'title': f"{today} {int(summary.get('hour', 0)):02d}:00 小时摘要",
            'excerpt': text,
            'appName': None,
            'browserUrl': None,
            'duration': summary.get('total_duration'),
            'score': score,
        })

    if report:
        score = _score_text(query, report.get('content') or '')
        if score > 0:
            items.append({
                'sourceType': 'daily_report',
                'sourceId': None,
                'date': report.get('date') or today,
                'timestamp': report.get('created_at') or 0,
                'title': f"{report.get('date') or today} 日报",
                'excerpt': (report.get('content') or '')[:220],
                'appName': None,
                'browserUrl': None,
                'duration': None,
                'score': score,
            })

    items.sort(key=lambda item: item.get('score', 0), reverse=True)
    return items[:limit]


def _normalize_endpoint(endpoint: str | None) -> str:
    return str(endpoint or '').strip().rstrip('/')


def _build_model_test_request(model_config: dict[str, Any]) -> tuple[str, dict[str, str], bytes]:
    provider = str(model_config.get('provider') or '').strip().lower()
    endpoint = _normalize_endpoint(model_config.get('endpoint'))
    api_key = str(model_config.get('api_key') or '').strip()
    model = str(model_config.get('model') or '').strip()

    if not endpoint:
        raise ValueError('请先填写 API 地址')
    if not model:
        raise ValueError('请先填写模型名称')

    headers = {'Content-Type': 'application/json'}

    if provider == 'claude':
        if not api_key:
            raise ValueError('请先填写 API 密钥')
        headers['x-api-key'] = api_key
        headers['anthropic-version'] = '2023-06-01'
        url = f'{endpoint}/v1/messages'
        body = {
            'model': model,
            'max_tokens': 16,
            'messages': [{'role': 'user', 'content': 'ping'}],
        }
        import json
        return url, headers, json.dumps(body).encode('utf-8')

    if provider in {'openai', 'deepseek', 'siliconflow', 'gemini', 'qwen', 'zhipu', 'moonshot', 'doubao', 'minimax'}:
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        url = f'{endpoint}/chat/completions'
        body = {
            'model': model,
            'messages': [{'role': 'user', 'content': 'ping'}],
            'max_tokens': 16,
        }
        import json
        return url, headers, json.dumps(body).encode('utf-8')

    if provider == 'ollama':
        url = f'{endpoint}/api/generate'
        body = {
            'model': model,
            'prompt': 'ping',
            'stream': False,
        }
        import json
        return url, headers, json.dumps(body).encode('utf-8')

    raise ValueError('当前提供商暂不支持连接测试')


def test_model_connection(model_config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = model_config or {}
    url, headers, data = _build_model_test_request(config)
    started_at = time.perf_counter()
    req = request.Request(url, data=data, headers=headers, method='POST')

    try:
        with request.urlopen(req, timeout=12) as response:
            response.read()
    except error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='ignore').strip()
        message = detail or f'HTTP {exc.code}'
        return {
            'success': False,
            'message': message[:240],
            'response_time_ms': int((time.perf_counter() - started_at) * 1000),
        }
    except Exception as exc:
        return {
            'success': False,
            'message': str(exc) or '连接失败',
            'response_time_ms': int((time.perf_counter() - started_at) * 1000),
        }

    return {
        'success': True,
        'message': '连接测试通过',
        'response_time_ms': int((time.perf_counter() - started_at) * 1000),
    }


def chat_work_assistant(question: str, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    trimmed = (question or '').strip()
    if not trimmed:
        return {
            'answer': '请输入你想问的问题。',
            'references': [],
            'usedAi': False,
            'modelName': None,
            'toolLabels': ['记忆检索'],
            'cards': [],
        }

    references = search_memory(trimmed, limit=8)
    today = datetime.now().strftime('%Y-%m-%d')
    timeline = get_timeline(today, limit=20, offset=0)
    hourly = get_hourly_summaries(today)
    report = get_report(today)

    answer_lines = [f"基于当前工作记录，我先给你结论：{trimmed} 相关的信息已整理如下。", ""]

    if references:
        answer_lines.append('### 相关依据')
        for item in references[:5]:
            duration_text = _format_duration(item.get('duration')) if item.get('duration') is not None else '无时长'
            answer_lines.append(f"- {item.get('title')}（{item.get('sourceType')}，{duration_text}）")
            if item.get('excerpt'):
                answer_lines.append(f"  - {item.get('excerpt')}")
    else:
        answer_lines.append('### 相关依据')
        answer_lines.append('- 当前没有检索到直接匹配的记录，我给你补充今天的概况。')

    answer_lines.extend(['', '### 今天概况'])
    answer_lines.append(f"- 活动记录：{len(timeline)} 条")
    answer_lines.append(f"- 小时摘要：{len(hourly)} 条")
    answer_lines.append(f"- 今日日报：{'已生成' if report else '未生成'}")

    if timeline:
        latest = timeline[0]
        answer_lines.append('')
        answer_lines.append('### 最近一条活动')
        answer_lines.append(
            f"- {latest.get('app_name') or '未知应用'} / {(latest.get('window_title') or '无标题')[:80]} / {_format_duration(latest.get('duration'))}"
        )
        if latest.get('browser_url'):
            answer_lines.append(f"- URL: {latest.get('browser_url')}")

    return {
        'answer': '\n'.join(answer_lines),
        'references': references,
        'usedAi': False,
        'modelName': None,
        'toolLabels': ['记忆检索'],
        'cards': [],
    }
