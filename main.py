import asyncio
import random
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

# ========= 可調整參數 =========
URL = "https://cis.ncu.edu.tw/HumanSys/student/stdSignIn"
WAIT_SECONDS = 20  # 給你手動登入時間
USER_DATA_DIR = "./user_data"  # 瀏覽器資料夾（持久化）
EIGHT_HOURS = 8 * 60 * 60  # 8小時

# ========= 模擬人類延遲 =========
async def human_delay(min_ms=500, max_ms=2000):
    delay = random.uniform(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)

# ========= 模擬滑鼠移動 =========
async def human_mouse_move(page):
    for _ in range(random.randint(3, 6)):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        await page.mouse.move(x, y, steps=random.randint(10, 30))
        await human_delay(100, 500)

# ========= 你的自動流程（貼上錄製的code） =========
async def run_automation(page):
    # 步驟零：確認目前在正確頁面，否則先導航過去
    if not page.url.startswith(URL):
        print(f"🔀 目前頁面不是目標頁，切換至 {URL}")
        await page.goto(URL)
        await human_delay(1000, 3000)

    await page.wait_for_selector("role=link[name='新增簽到']")
    await human_delay()

    await page.get_by_role("link", name="新增簽到").click()
    await human_delay()


    # 等到上午 8:00–9:00 之間的隨機時間才執行第一步
    now = datetime.now()
    target = now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(seconds=random.randint(0, 3600))
    if now >= target:
        # 今天的時間窗口已過，等到明天
        target += timedelta(days=1)
    wait_seconds = (target - now).total_seconds()
    print(f"⏰ 目前時間：{now.strftime('%H:%M:%S')}，將於 {target.strftime('%m/%d %H:%M:%S')} 開始執行（等待 {wait_seconds/3600:.1f} 小時）")
    await asyncio.sleep(wait_seconds)

    print(f"🚀 開始執行自動流程：{datetime.now().strftime('%H:%M:%S')}")

    await page.get_by_role("button", name="更新時間").click()
    print(f"🕐 更新時間：{datetime.now().strftime('%H:%M:%S')}")
    await human_delay()

    await page.get_by_role("button", name="簽到").click()
    sign_in_time = datetime.now()
    wait_seconds = EIGHT_HOURS + random.randint(0, 60 * 60)  # 8~9 小時
    sign_out_time = sign_in_time + timedelta(seconds=wait_seconds)
    print(f"✅ 簽到：{sign_in_time.strftime('%H:%M:%S')}，預計簽退：{sign_out_time.strftime('%H:%M:%S')}（間隔 {wait_seconds/3600:.2f} 小時）")
    await asyncio.sleep(wait_seconds)


    await page.get_by_role("button", name="更新時間").click()
    print(f"🕐 更新時間：{datetime.now().strftime('%H:%M:%S')}")
    await human_delay()


    await page.get_by_role("button", name="簽退").click()
    print(f"✅ 簽退：{datetime.now().strftime('%H:%M:%S')}")
    await human_delay()



    print("✅ 自動流程完成")

# ========= 主流程 =========
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

        print(f"🌐 打開登入頁：{URL}")
        await page.goto(URL)

        print(f"⏳ 請在 {WAIT_SECONDS} 秒內完成登入...")
        await asyncio.sleep(WAIT_SECONDS)

        print("🔍 準備執行自動流程")

        try:
            await run_automation(page)
        except Exception as e:
            print("❌ 自動流程錯誤：", e)

        print("🟢 程式持續運行（可保持登入狀態）")
        while True:
            await asyncio.sleep(86400)


if __name__ == "__main__":
    asyncio.run(main())