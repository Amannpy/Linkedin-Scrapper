import asyncio
from core import BrowserManager

async def test():
    browser = BrowserManager()
    try:
        await browser.initialize()
        print("✓ Browser initialized successfully!")
    finally:
        await browser.close()

asyncio.run(test())