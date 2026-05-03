import asyncio
import random
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

# ========= 可調整參數 =========
# 要改 EIGHT_HOURS 和 DAEIGHT_HOURSY_OF_WORK ###########################################
TARGET_URL = "https://cis.ncu.edu.tw/HumanSys/student/stdSignIn"
USER_DATA_DIR = "./user_data"  # 瀏覽器資料夾（持久化）
EIGHT_HOURS = 8 * 60 * 60  # 8小時
work_plan = [
    "熟悉系統架構、開發環境建置、權限確認",
    "閱讀既有程式碼與文件，釐清主要模組功能",
    "整理需求、規劃未來",
    "盤點舊功能問題與技術債，部份修正",
    "實做徵才網雙語化",
    "實做徵才網雙語化",
    "實做徵才網雙語化",
    "持續開發與測試，修正回報問題",
    "持續開發與測試，修正回報問題",
    "執行版本、安全性檢查",
    "設計 AI 工作流程初版",
    "實作簡單 AI prototype",
    "與行政單位測試 AI 工具可行性",
    "優化 AI 流程與回應品質",
    "整理內部文件（操作說明 / API / 流程）",
    "持續維護舊功能與修復問題",
    "規劃第二階段優化（效能 / UX）",
    "提供行政人員技術支援與使用教學",
    "整合 AI 工具至實際系統或工作流程",
    "回顧與整理成果，規劃後續開發方向"
]
# ========= 模擬人類延遲 =========
async def human_delay(min_ms=500, max_ms=3000):
    delay = random.uniform(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)

# ======== 確認已進入人事管理系統 =========
async def ensure_in_target_url(page):
    while not page.url.startswith(TARGET_URL):
        await human_delay(1000, 2000)
        print(f"🔀 目前頁面不是目標頁，切換至 {TARGET_URL}")
        await page.goto(TARGET_URL)
        await human_delay(3000, 5000)

        if page.url.startswith("https://portal.ncu.edu.tw/login"):
            print("🔐 偵測到 Portal 登入頁，嘗試登入中...")
            await handle_log_in(page)
            continue
        if page.url.startswith("https://portal.ncu.edu.tw/timeout"):
            print("⌛ 偵測到 Portal timeout 頁面，嘗試處理中...")
            await handle_timeout_page(page)
            continue
        if page.url.startswith("https://portal.ncu.edu.tw/oauth"):
            print("🔐 偵測到 OAuth 跳轉頁，嘗試處理中...")
            await handle_oauth_page(page)
            continue


    # 確認進入到簽到頁面
    if page.url.startswith(TARGET_URL):
        print("➡️ 已進入人事系統頁面")
    else:
        raise Exception("應該要在簽到頁面，但目前頁面 TARGET_URL 是：" + page.url)



async def handle_log_in(page):
    # 嘗試偵測是否有記住帳號資訊的隱藏欄位
    remembered_username = page.locator('input[type="hidden"][name="username"]')
    remembered_account = page.locator('input[type="hidden"][name="remember-as"]')
    has_remembered_username = await remembered_username.count() > 0
    has_remembered_account = await remembered_account.count() > 0

    if has_remembered_username and has_remembered_account:
        print("🔑 偵測到已記住帳號資訊，嘗試按下「登入 Portal」")
        await page.wait_for_selector("role=button[name='登入 Portal']")
        await page.get_by_role("button", name="登入 Portal").click()            
        await human_delay(3000, 5000)

    # 如果沒有記住帳號資訊，或按下登入後仍在登入頁，則提示使用者手動登入
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

            if account_value == "" or password_value == "":
                print("🔍 偵測到帳號/密碼輸入欄位為空，尚未有登入 session，請先手動登入")
                input("請完成登入後按下 Enter 繼續...")
                await human_delay(3000, 5000)



async def handle_timeout_page(page):
    back_to_system_btn = page.get_by_role("button", name="回到系統")
    back_to_system_btn_exists = await back_to_system_btn.count() > 0
    if await back_to_system_btn_exists:
        await human_delay()
        print("🖱️ 嘗試按下「回到系統」")
        await back_to_system_btn.click()
        await human_delay(3000, 5000)
    else:
        print("⚠️ 找不到「回到系統」按鈕，改為導向目標頁面")
        await page.goto(TARGET_URL)
        await human_delay(3000, 5000)


async def handle_oauth_page(page):
    go_btn = page.get_by_role("button", name="前往")
    go_btn_exists = await go_btn.count() > 0
    if go_btn_exists:
        print("🖱️ 嘗試按下「前往」")
        await human_delay()
        await go_btn.first.click()
        await human_delay(3000, 5000)
    else:
        # todo: 未來可以在這邊通知使用者
        input("⚠️ 找不到「前往」按鈕，請手動處理完成後按下 Enter 繼續...")


# ========= 你的自動流程（貼上錄製的code） =========
async def run_automation(page, work_message):

    # 簽到流程
    await ensure_in_target_url(page)
    await page.wait_for_selector("role=link[name='新增簽到']")
    await page.get_by_role("link", name="新增簽到").click()
    await human_delay()


    # await 確認簽到簽退狀態
    # await 簽到流程
    # await 簽退流程
    

    await page.wait_for_selector("role=button[name='更新時間']")
    await page.get_by_role("button", name="更新時間").click()
    print(f"🕐 更新時間：{datetime.now().strftime('%H:%M:%S')}")
    await human_delay()
    
    await page.wait_for_selector("role=button[name='簽到']")
    await page.get_by_role("button", name="簽到").click()
    sign_in_time = datetime.now()
    print(f"✅ 簽到：{sign_in_time.strftime('%H:%M:%S')}")
    await human_delay()

    wait_seconds = EIGHT_HOURS + random.randint(0, 30 * 60)  # 8~8.5 小時
    sign_out_time = sign_in_time + timedelta(seconds=wait_seconds)
    print(f"⏰預計簽退：{sign_out_time.strftime('%H:%M:%S')}（間隔 {wait_seconds/3600:.2f} 小時）")
    await asyncio.sleep(wait_seconds)

    # 簽退流程
    await ensure_in_target_url(page)
    await human_delay()
    
    await page.wait_for_selector("#AttendWork")
    await page.locator("#AttendWork").click()
    await human_delay()
    
    await page.locator("#AttendWork").fill(work_message)
    print(f"📝 工作內容：{work_message}")
    await human_delay()

    await page.wait_for_selector("role=button[name='更新時間']")
    await page.get_by_role("button", name="更新時間").click()
    print(f"🕐 更新時間：{datetime.now().strftime('%H:%M:%S')}")
    await human_delay()
    
    await page.wait_for_selector("role=button[name='簽退']")
    await page.get_by_role("button", name="簽退").click()
    sign_out_time = datetime.now()
    print(f"✅ 簽退：{sign_out_time.strftime('%H:%M:%S')}")
    await human_delay(3000, 5000)



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

        # 預打工內容，避免簽退時才打字
        day_of_work = int(input("今天是第幾天上班？請輸入數字後按 Enter："))
        suggested_work_message = work_plan[day_of_work - 1] if 1 <= day_of_work <= len(work_plan) else ""
        print(f"建議的工作日誌內容：{suggested_work_message}")
        while True:
            use_suggested_answer = input("是否使用建議的工作內容？輸入 y 使用建議內容，輸入其他則自行輸入：").strip().lower()
            if use_suggested_answer == 'y':
                # use suggested_work_message, that is work_plan[day_of_work - 1]
                break
            elif use_suggested_answer == 'n':
                custom_message = input("請輸入今天的工作內容：")
                work_plan[day_of_work - 1] = custom_message
                break
            else:
                print("只接受 y 或 n，重新再試一次")
                continue
                
        work_message = suggested_work_message if use_suggested_answer == 'y' else custom_message

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
        
        try:
            await run_automation(page, work_message)
            print("👌 自動簽到流程完成 (等待使用者確認後關閉)")
        except Exception as e:
            print("❌ 自動流程錯誤：", e)

        
        input("按下 Enter 鍵結束程式...")

if __name__ == "__main__":
    asyncio.run(main())