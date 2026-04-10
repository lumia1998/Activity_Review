"""OCR 文字识别服务 - 支持 PaddleOCR 和 Windows PowerShell OCR"""
from __future__ import annotations

import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

from .config_service import load_config
from .ocr_log_service import append_ocr_log


_PADDLEOCR_INSTANCE = None
_OCR_SEMAPHORE = threading.Semaphore(2)

# 敏感文本正则模式
_SENSITIVE_PATTERNS = [
    re.compile(r'1[3-9]\d{9}'),
    re.compile(r'[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]'),
    re.compile(r'\b\d{16,19}\b'),
    re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
    re.compile(r'(?:password|passwd|密码|pwd)\s*[:：]\s*\S+', re.IGNORECASE),
]


def _get_paddleocr():
    global _PADDLEOCR_INSTANCE
    if _PADDLEOCR_INSTANCE is None:
        try:
            from paddleocr import PaddleOCR
            _PADDLEOCR_INSTANCE = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False, use_gpu=False)
        except Exception:
            return None
    return _PADDLEOCR_INSTANCE


def _ocr_paddleocr(image_path: str) -> str | None:
    ocr = _get_paddleocr()
    if ocr is None:
        return None
    try:
        result = ocr.ocr(image_path, cls=True)
        if not result or not result[0]:
            return None
        texts = [line[1][0] for line in result[0] if line and len(line) >= 2 and line[1]]
        return '\n'.join(texts) if texts else None
    except Exception:
        return None


def _ocr_windows_powershell(image_path: str) -> str | None:
    if sys.platform != 'win32':
        return None
    path = Path(image_path)
    if not path.exists():
        return None

    ps_script = f"""
$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$imagePath = '{str(path).replace("'", "''")}'

function Write-OcrJson($payload) {{
    Write-Output (ConvertTo-Json $payload -Depth 5 -Compress)
}}

function Write-OcrError([string]$message) {{
    Write-OcrJson @{{
        text = ""
        error = ([string]$message)
        boxes = @()
        confidence = 0
    }}
}}

[Windows.Media.Ocr.OcrEngine, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null
[Windows.Globalization.Language, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null
[Windows.System.UserProfile.GlobalizationPreferences, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' }})[0]
if ($null -eq $asTaskGeneric) {{
    Write-OcrError "System.WindowsRuntimeSystemExtensions.AsTask 未找到"
    exit
}}

Function Await($WinRtTask, $ResultType) {{
    if ($null -eq $WinRtTask) {{
        throw "WinRT 异步任务为空: $ResultType"
    }}
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}}

try {{
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($imagePath)) ([Windows.Storage.StorageFile])
    if ($null -eq $file) {{ throw "读取截图文件失败: $imagePath" }}

    $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    if ($null -eq $stream) {{ throw "打开截图流失败: $imagePath" }}

    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    if ($null -eq $bitmap) {{ throw "解码截图失败: $imagePath" }}

    $ocrBitmap = [Windows.Graphics.Imaging.SoftwareBitmap]::Convert(
        $bitmap,
        [Windows.Graphics.Imaging.BitmapPixelFormat]::Bgra8,
        [Windows.Graphics.Imaging.BitmapAlphaMode]::Premultiplied
    )
    if ($null -eq $ocrBitmap) {{ throw "转换 OCR 位图失败: $imagePath" }}

    $ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    if ($ocrEngine -eq $null) {{
        foreach ($langTag in @('zh-Hans', 'zh-Hans-CN', 'en-US')) {{
            try {{
                $language = [Windows.Globalization.Language]::new($langTag)
                $candidate = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($language)
                if ($candidate -ne $null) {{
                    $ocrEngine = $candidate
                    break
                }}
            }} catch {{}}
        }}
    }}

    if ($ocrEngine -eq $null) {{
        Write-OcrError "No OCR engine available"
        exit
    }}

    $result = Await ($ocrEngine.RecognizeAsync($ocrBitmap)) ([Windows.Media.Ocr.OcrResult])
    if ($null -eq $result) {{ throw "OCR 结果为空" }}

    $allText = @()
    foreach ($line in $result.Lines) {{
        $allText += $line.Text
    }}

    Write-OcrJson @{{
        text = ($allText -join "`n")
        boxes = @()
        confidence = 0.9
    }}
}} catch {{
    $message = if ($_.Exception -and $_.Exception.Message) {{ [string]$_.Exception.Message }} else {{ [string]$_ }}
    Write-OcrError $message
}}
"""

    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Sta', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=25,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    output = (result.stdout or '').strip()
    if not output:
        return None

    try:
        import json
        payload = json.loads(output)
    except Exception:
        return None

    if payload.get('error'):
        return None

    text = str(payload.get('text') or '').strip()
    return text or None


def _ocr_easyocr(image_path: str) -> str | None:
    try:
        import easyocr
        reader = easyocr.Reader(['ch_sim', 'en'], verbose=False)
        results = reader.readtext(image_path)
        if not results:
            return None
        texts = [item[1] for item in results if item and len(item) >= 2]
        return '\n'.join(texts) if texts else None
    except Exception:
        return None


def perform_ocr(image_path: str) -> str | None:
    if not image_path or not Path(image_path).exists():
        return None

    config = load_config()
    storage = config.get('storage') or {}
    if storage.get('ocr_enabled', True) is False:
        return None

    with _OCR_SEMAPHORE:
        text = _ocr_paddleocr(image_path)
        engine = 'paddleocr' if text else None
        if not text and sys.platform == 'win32':
            text = _ocr_windows_powershell(image_path)
            engine = 'windows_ocr' if text else engine
        if not text:
            text = _ocr_easyocr(image_path)
            engine = 'easyocr' if text else engine

        append_ocr_log({
            'imagePath': image_path,
            'success': bool(text),
            'engine': engine,
            'textPreview': (text or '')[:200],
        })
        return text


def filter_sensitive_text(text: str | None) -> str | None:
    if not text:
        return text
    config = load_config()
    privacy = config.get('privacy') or {}
    if not privacy.get('filter_sensitive', True):
        return text
    filtered = text
    for pattern in _SENSITIVE_PATTERNS:
        filtered = pattern.sub('***', filtered)
    for keyword in privacy.get('excluded_keywords') or []:
        if keyword and keyword in filtered:
            filtered = filtered.replace(keyword, '***')
    return filtered


def is_ocr_available() -> dict[str, Any]:
    paddle = _get_paddleocr() is not None
    easyocr = False
    try:
        import easyocr
        easyocr = True
    except ImportError:
        pass
    windows_ocr = sys.platform == 'win32'
    return {
        'available': paddle or easyocr or windows_ocr,
        'engines': {'paddleocr': paddle, 'easyocr': easyocr, 'windows_ocr': windows_ocr},
        'recommended': 'paddleocr' if paddle else ('windows_ocr' if windows_ocr else ('easyocr' if easyocr else None)),
    }
