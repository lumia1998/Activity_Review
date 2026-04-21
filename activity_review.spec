# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Activity Review (Windows, onedir, no-console)."""

import os
import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = os.path.abspath('.')

# ── Icon ────────────────────────────────────────────────────────────────────
_ico_path = os.path.join(PROJECT_ROOT, 'public', 'icon.ico')
if not os.path.exists(_ico_path):
    _ico_path = None  # build without icon if .ico hasn't been generated

# ── Data files ──────────────────────────────────────────────────────────────
# Bundle the Vite-built frontend (dist/) into the package root.
datas = [
    (os.path.join(PROJECT_ROOT, 'dist'), 'dist'),
]

# ── Hidden imports ──────────────────────────────────────────────────────────
# PyInstaller cannot detect all dynamic imports used by FastAPI / uvicorn.
hiddenimports = [
    # --- uvicorn internals ---
    'uvicorn',
    'uvicorn.config',
    'uvicorn.main',
    'uvicorn.server',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.loops.asyncio',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.http.httptools_impl',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.protocols.websockets.wsproto_impl',
    'uvicorn.protocols.websockets.websockets_impl',
    'uvicorn.logging',

    # --- FastAPI / Starlette / Pydantic ---
    'fastapi',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'starlette',
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',
    'starlette.responses',
    'starlette.staticfiles',
    'pydantic',
    'pydantic.deprecated',
    'pydantic.deprecated.decorator',

    # --- h11 / httptools / websockets ---
    'h11',
    'httptools',
    'websockets',
    'wsproto',

    # --- backend application ---
    'backend',
    'backend.app',
    'backend.app.main',
    'backend.app.core',
    'backend.app.core.paths',
    'backend.app.api',
    'backend.app.api.assistant',
    'backend.app.api.config',
    'backend.app.api.files',
    'backend.app.api.intelligence',
    'backend.app.api.reports',
    'backend.app.api.runtime',
    'backend.app.api.stats',
    'backend.app.api.system_api',
    'backend.app.api.timeline',
    'backend.app.services',
    'backend.app.services.ai_service',
    'backend.app.services.app_classifier_service',
    'backend.app.services.assistant_service',
    'backend.app.services.autostart_service',
    'backend.app.services.base',
    'backend.app.services.browser_service',
    'backend.app.services.config_service',
    'backend.app.services.data_service',
    'backend.app.services.hourly_service',
    'backend.app.services.idle_service',
    'backend.app.services.monitor_service',
    'backend.app.services.ocr_log_service',
    'backend.app.services.ocr_service',
    'backend.app.services.permission_service',
    'backend.app.services.providers',
    'backend.app.services.providers.common',
    'backend.app.services.providers.windows',
    'backend.app.services.report_service',
    'backend.app.services.report_store_service',
    'backend.app.services.runtime_service',
    'backend.app.services.screenshot_service',
    'backend.app.services.update_service',
    'backend.app.services.work_intelligence_service',

    # --- desktop shell ---
    'desktop',
    'desktop.main',
    'desktop.tray',
    'desktop.single_instance',
    'desktop.windows',

    # --- pywebview ---
    'webview',
    'webview.window',
    'webview.event',
    'webview.menu',
    'webview.screen',
    'webview.util',
    'webview.http',
    'webview.dom',
    'webview.errors',
    'webview.platforms',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',

    # --- pythonnet / clr (required by pywebview winforms) ---
    'clr',
    'clr_loader',
    'pythonnet',

    # --- system / runtime deps ---
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'pystray',
    'pystray._win32',
    'mss',
    'mss.windows',
    'sqlite3',
    'multiprocessing',
    'email.mime.multipart',
    'email.mime.text',

    # --- anyio (used by starlette) ---
    'anyio',
    'anyio._backends',
    'anyio._backends._asyncio',
    'sniffio',
]

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'launcher.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'numpy',
        'pandas',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ActivityReview',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_ico_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ActivityReview',
)
