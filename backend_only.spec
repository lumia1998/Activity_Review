# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Activity Review Backend only (Windows, onedir, no-console)."""

import os

block_cipher = None

PROJECT_ROOT = os.path.abspath('.')

# ── Data files ──────────────────────────────────────────────────────────────
datas = [
    (os.path.join(PROJECT_ROOT, 'dist'), 'dist'),
]

# ── Hidden imports ──────────────────────────────────────────────────────────
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

    # --- system / runtime deps ---
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
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
    [os.path.join(PROJECT_ROOT, 'backend_server.py')],
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
        'webview',
        'pystray',
        'desktop',
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
    name='ActivityReviewBackend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ActivityReviewBackend',
)
