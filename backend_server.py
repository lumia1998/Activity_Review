import sys
import asyncio
import platform

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

def main():
    uvicorn.run(
        'backend.app.main:app',
        host='127.0.0.1',
        port=8000,
        log_level='info',
    )

if __name__ == '__main__':
    main()
