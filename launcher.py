import sys
import os
import traceback
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else '.', 'activity_review_debug.log'), encoding='utf-8'),
    ]
)

logger = logging.getLogger(__name__)

try:
    logger.info('Launcher starting, frozen=%s', getattr(sys, 'frozen', False))
    logger.info('sys.executable=%s', sys.executable)
    logger.info('sys._MEIPASS=%s', getattr(sys, '_MEIPASS', 'N/A'))

    from desktop.main import main
    main()
except Exception as e:
    logger.critical('Fatal error: %s', e)
    logger.critical(traceback.format_exc())
    if getattr(sys, 'frozen', False):
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"启动失败:\n{e}\n\n详见 activity_review_debug.log", "Activity Review Error", 0x10)
    sys.exit(1)
