import asyncio    
from playwright.async_api import async_playwright

from main import USER_DATA_DIR

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            viewport={"width": 1280, "height": 800},
            locale="zh-TW",
            timezone_id="Asia/Taipei",
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # 避免 webdriver 被檢測
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        await page.goto("https://portal.ncu.edu.tw/login")

        # 等待登入頁面加載完成
        await page.wait_for_load_state("networkidle")

        input("請在瀏覽器中完成登入後，按下 Enter 鍵繼續...")

if __name__ == "__main__":
    asyncio.run(main())