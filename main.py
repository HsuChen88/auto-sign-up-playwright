import asyncio
import random
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

# ========= 可調整參數 =========
URL = "https://cis.ncu.edu.tw/HumanSys/student/stdSignIn"
WAIT_SECONDS = 10  # 給你手動登入時間
USER_DATA_DIR = "./user_data"  # 瀏覽器資料夾（持久化）
EIGHT_HOURS = 8 * 60 * 60  # 8小時

# ========= 模擬人類延遲 =========
async def human_delay(min_ms=500, max_ms=2000):
    delay = random.uniform(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)

# ======== 確認已進入人事管理系統 =========
async def ensure_now_in_target_url(page) -> bool:
    while not page.url.startswith(URL) and await ensure_logged_in(page):
        print(f"🔀 目前頁面不是目標頁，切換至 {URL}")
        await page.goto(URL)
        await human_delay(3000, 5000)
        # 可能遇到跳轉 Oauth 頁面，需要按下「前往」按鈕
        on_oauth_next = page.url.startswith("https://portal.ncu.edu.tw/oauth/next")
        go_btn = page.get_by_role("button", name="前往")
        go_btn_exists = await go_btn.count() > 0

        if on_oauth_next or go_btn_exists:
            if go_btn_exists:
                print("➡️ 偵測到跳轉頁，按下「前往」")
                await go_btn.first.click()
                await human_delay(3000, 5000)
            else:
                raise Exception("找不到「前往」按鈕")

    return True


async def ensure_logged_in(page) -> bool:
    try:
        if page.url.startswith("https://portal.ncu.edu.tw/login"):
            print("🔐 目前在 Portal 登入頁，檢查是否已有登入 session")

            while True:
                if page.url.startswith("https://portal.ncu.edu.tw/timeout"):
                    print("⌛ 偵測到 Portal timeout 頁面，先嘗試按下「回到系統」")
                    await human_delay()

                    back_to_system_btn = page.get_by_role("button", name="回到系統")
                    if await back_to_system_btn.count() > 0:
                        await back_to_system_btn.click()
                        await human_delay(3000, 5000)
                    else:
                        print("⚠️ 找不到「回到系統」按鈕，改為導向登入頁")
                        await page.goto("https://portal.ncu.edu.tw/login")
                        await human_delay(3000, 5000)
               
               
                account_box = page.get_by_role("textbox", name="帳號")
                password_box = page.get_by_role("textbox", name="密碼")
                account_exists = await account_box.count() > 0
                password_exists = await password_box.count() > 0

                if account_exists and password_exists:
                    account_visible = await account_box.first.is_visible()
                    password_visible = await password_box.first.is_visible()

                    if account_visible and password_visible:
                        account_value = (await account_box.first.input_value()).strip()
                        password_value = (await password_box.first.input_value()).strip()

                        if account_value == "" and password_value == "":
                            print("🔍 偵測到帳號/密碼輸入欄位為空，尚未有登入 session，請先手動登入")
                        else:
                            print("⌛ 偵測到登入欄位仍存在（可能正在輸入或自動填入），等待登入完成")

                        print(f"⏳ {WAIT_SECONDS} 秒後再次確認登入狀態...")
                        await asyncio.sleep(WAIT_SECONDS)
                        continue

                else: 
                    print("✅ 偵測到已登入 session，嘗試按下「登入 Portal」")
                    login_portal_btn = page.get_by_role("button", name="登入 Portal")
                    await human_delay()
                    await login_portal_btn.click()
                    await human_delay(3000, 5000)
                    break
                
        return True
    except Exception as e:
        print(f"❌ 確認 Portal 狀態失敗：{e}")
        return False

# ========= 你的自動流程（貼上錄製的code） =========
async def run_automation(page):

    if await ensure_now_in_target_url(page):
        # 進入簽到頁面
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

        await page.get_by_role("button", name="更新時間").click()
        print(f"🕐 更新時間：{datetime.now().strftime('%H:%M:%S')}")
        await human_delay()

        # await page.get_by_role("button", name="簽到").click()
        sign_in_time = datetime.now()
        wait_seconds = EIGHT_HOURS + random.randint(0, 60 * 60)  # 8~9 小時
        sign_out_time = sign_in_time + timedelta(seconds=wait_seconds)
        print(f"✅ 簽到：{sign_in_time.strftime('%H:%M:%S')}，預計簽退：{sign_out_time.strftime('%H:%M:%S')}（間隔 {wait_seconds/3600:.2f} 小時）")
        await asyncio.sleep(wait_seconds)

    print(f"😴 等待中... (請不要中斷程式)")

    if await ensure_now_in_target_url(page):
        await page.get_by_role("button", name="更新時間").click()
        print(f"🕐 更新時間：{datetime.now().strftime('%H:%M:%S')}")
        await human_delay()

        await page.get_by_role("button", name="簽退").click()
        print(f"✅ 簽退：{datetime.now().strftime('%H:%M:%S')}")
        await human_delay()

    print("👌 自動簽到流程完成")

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

        print(f"🚀 開始執行自動流程：{datetime.now().strftime('%H:%M:%S')}")
        try:
            await run_automation(page)
        except Exception as e:
            print("❌ 自動流程錯誤：", e)

        print("🟢 程式持續運行（等待使用者確認後手動關閉）")
        while True:
            await asyncio.sleep(86400)


if __name__ == "__main__":
    asyncio.run(main())