"""AI 服务 - 统一的 AI 模型调用层，支持多种提供商"""
from __future__ import annotations

import json
import time
from typing import Any
from urllib import error, request

from .config_service import load_config


def _normalize_endpoint(endpoint: str | None) -> str:
    return str(endpoint or '').strip().rstrip('/')


def _get_active_model_profile() -> dict[str, Any] | None:
    """获取当前激活的 AI 模型配置"""
    config = load_config()
    profiles = config.get('text_model_profiles') or []
    active_name = config.get('active_model_profile') or ''
    if active_name:
        for profile in profiles:
            if profile.get('name') == active_name:
                return profile
    # 返回第一个可用配置
    if profiles:
        return profiles[0]

    # 兼容旧配置格式
    provider = config.get('ai_provider') or config.get('provider') or ''
    endpoint = config.get('ai_endpoint') or config.get('endpoint') or ''
    api_key = config.get('ai_api_key') or config.get('api_key') or ''
    model = config.get('ai_model') or config.get('model') or ''

    if endpoint and model:
        return {
            'provider': provider,
            'endpoint': endpoint,
            'api_key': api_key,
            'model': model,
        }

    return None


def _build_chat_request(
    model_config: dict[str, Any],
    messages: list[dict[str, str]],
    max_tokens: int = 2048,
    temperature: float = 0.7,
) -> tuple[str, dict[str, str], bytes]:
    """构建 AI 请求

    Returns:
        (url, headers, body_bytes)
    """
    provider = str(model_config.get('provider') or '').strip().lower()
    endpoint = _normalize_endpoint(model_config.get('endpoint'))
    api_key = str(model_config.get('api_key') or '').strip()
    model = str(model_config.get('model') or '').strip()

    if not endpoint:
        raise ValueError('请先配置 AI 接口地址')
    if not model:
        raise ValueError('请先配置模型名称')

    headers = {'Content-Type': 'application/json'}

    if provider == 'claude':
        if not api_key:
            raise ValueError('请先填写 API 密钥')
        headers['x-api-key'] = api_key
        headers['anthropic-version'] = '2023-06-01'
        url = f'{endpoint}/v1/messages'
        body = {
            'model': model,
            'max_tokens': max_tokens,
            'messages': messages,
        }
        return url, headers, json.dumps(body).encode('utf-8')

    # OpenAI 兼容格式（适用于大多数提供商）
    if provider in {'openai', 'deepseek', 'siliconflow', 'gemini', 'qwen',
                    'zhipu', 'moonshot', 'doubao', 'minimax', 'ollama'}:
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        if provider == 'ollama':
            url = f'{endpoint}/api/chat'
            body = {
                'model': model,
                'messages': messages,
                'stream': False,
                'options': {'temperature': temperature},
            }
        else:
            url = f'{endpoint}/chat/completions'
            body = {
                'model': model,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature,
            }

        return url, headers, json.dumps(body).encode('utf-8')

    # 默认 OpenAI 格式
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    url = f'{endpoint}/chat/completions'
    body = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
    }
    return url, headers, json.dumps(body).encode('utf-8')


def _parse_ai_response(provider: str, response_body: str) -> str | None:
    """解析 AI 响应，提取文本内容"""
    try:
        data = json.loads(response_body)
    except (json.JSONDecodeError, TypeError):
        return None

    if provider == 'claude':
        # Claude API 响应格式
        content = data.get('content') or []
        texts = [item.get('text', '') for item in content if item.get('type') == 'text']
        return '\n'.join(texts) if texts else None

    # Ollama API 响应格式
    if provider == 'ollama':
        return data.get('message', {}).get('content') or data.get('response')

    # OpenAI 兼容格式
    choices = data.get('choices') or []
    if choices:
        message = choices[0].get('message') or {}
        return message.get('content')

    return None


def call_ai(
    messages: list[dict[str, str]],
    model_config: dict[str, Any] | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    timeout: int = 60,
) -> dict[str, Any]:
    """调用 AI 模型

    Args:
        messages: 对话消息列表
        model_config: 模型配置，None 使用默认配置
        max_tokens: 最大生成 token 数
        temperature: 温度参数
        timeout: 超时秒数

    Returns:
        {'content': str, 'model': str, 'provider': str, 'response_time_ms': int}
    """
    config = model_config or _get_active_model_profile()
    if config is None:
        return {
            'content': None,
            'model': None,
            'provider': None,
            'response_time_ms': 0,
            'error': '未配置 AI 模型，请在设置中配置',
        }

    provider = str(config.get('provider') or '').strip().lower()
    model = str(config.get('model') or '').strip()

    try:
        url, headers, body = _build_chat_request(config, messages, max_tokens, temperature)
    except ValueError as exc:
        return {
            'content': None,
            'model': model,
            'provider': provider,
            'response_time_ms': 0,
            'error': str(exc),
        }

    started_at = time.perf_counter()
    req = request.Request(url, data=body, headers=headers, method='POST')

    try:
        with request.urlopen(req, timeout=timeout) as response:
            response_body = response.read().decode('utf-8', errors='ignore')
    except error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='ignore').strip()
        return {
            'content': None,
            'model': model,
            'provider': provider,
            'response_time_ms': int((time.perf_counter() - started_at) * 1000),
            'error': detail or f'HTTP {exc.code}',
        }
    except Exception as exc:
        return {
            'content': None,
            'model': model,
            'provider': provider,
            'response_time_ms': int((time.perf_counter() - started_at) * 1000),
            'error': str(exc) or '连接失败',
        }

    content = _parse_ai_response(provider, response_body)
    elapsed = int((time.perf_counter() - started_at) * 1000)

    return {
        'content': content,
        'model': model,
        'provider': provider,
        'response_time_ms': elapsed,
        'error': None,
    }


def generate_ai_report(
    date: str,
    base_report: str,
    custom_prompt: str | None = None,
    locale: str = 'zh-CN',
) -> dict[str, Any]:
    """使用 AI 增强日报

    Args:
        date: 日期
        base_report: 基础模板报告内容
        custom_prompt: 用户自定义提示词
        locale: 语言

    Returns:
        {'content': str, 'model': str, 'error': str | None}
    """
    config = load_config()
    model_config = _get_active_model_profile()

    if model_config is None:
        return {
            'content': base_report,
            'model': None,
            'error': '未配置 AI 模型',
        }

    locale_instruction = '请用中文回答' if locale.startswith('zh') else 'Please respond in English'

    system_prompt = f"""你是一位工作日志分析助手。你的任务是基于用户的工作活动数据，生成一份结构清晰、有洞察力的工作日报。

{locale_instruction}

要求：
1. 保留原始报告中的所有统计数据和关键信息
2. 增加对工作模式的分析和洞察
3. 识别工作中的亮点和可能的改进空间
4. 语言简洁专业，避免冗余
5. 使用 Markdown 格式输出"""

    if custom_prompt and custom_prompt.strip():
        system_prompt += f'\n\n用户额外要求：{custom_prompt.strip()}'

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': f'请基于以下工作数据生成 {date} 的工作日报：\n\n{base_report}'},
    ]

    result = call_ai(messages, model_config, max_tokens=4096, temperature=0.5)
    return {
        'content': result.get('content') or base_report,
        'model': result.get('model'),
        'error': result.get('error'),
    }


def ai_chat_assistant(
    question: str,
    context_text: str,
    history: list[dict[str, str]] | None = None,
    locale: str = 'zh-CN',
) -> dict[str, Any]:
    """AI 助手对话

    Args:
        question: 用户问题
        context_text: 上下文（活动记录、摘要等）
        history: 对话历史
        locale: 语言

    Returns:
        {'answer': str, 'model': str, 'usedAi': bool}
    """
    model_config = _get_active_model_profile()
    if model_config is None:
        return {
            'answer': '未配置 AI 模型，无法回答。请在设置中配置 AI 模型。',
            'model': None,
            'usedAi': False,
            'error': '未配置 AI 模型',
        }

    locale_instruction = '请用中文回答' if locale.startswith('zh') else 'Please respond in English'

    messages = [
        {
            'role': 'system',
            'content': f'你是一位智能工作助手，帮助用户回顾和分析他们的工作记录。{locale_instruction}\n\n以下是用户的工作数据：\n{context_text}',
        },
    ]

    # 加入历史对话
    if history:
        for msg in history[-10:]:  # 最多保留最近10条
            role = msg.get('role') or 'user'
            content = msg.get('content') or ''
            if content:
                messages.append({'role': role, 'content': content})

    messages.append({'role': 'user', 'content': question})

    result = call_ai(messages, model_config, max_tokens=2048, temperature=0.7)
    return {
        'answer': result.get('content') or '抱歉，无法生成回答。',
        'model': result.get('model'),
        'usedAi': result.get('error') is None,
        'error': result.get('error'),
    }
