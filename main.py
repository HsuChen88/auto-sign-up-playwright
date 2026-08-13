import asyncio
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

# ========= 可調整參數 =========
TARGET_URL = "https://cis.ncu.edu.tw/HumanSys/student/stdSignIn"
USER_DATA_DIR = "./user_data"  # 瀏覽器資料夾（持久化）
TAIPEI_TZ = ZoneInfo("Asia/Taipei")
SECONDS_PER_HOUR = 60 * 60
SIGN_OUT_JITTER_SECONDS = 30 * 60


@dataclass(frozen=True)
class WorkPeriod:
    year: int
    month: int
    start_day: int
    end_day: int
    goal: str
    hours: int

    @property
    def start_date(self) -> date:
        return date(self.year, self.month, self.start_day)

    @property
    def end_date(self) -> date:
        return date(self.year, self.month, self.end_day)

    @property
    def seconds(self) -> int:
        return self.hours * SECONDS_PER_HOUR

    @property
    def label(self) -> str:
        return f"{self.start_date:%Y-%m-%d} ~ {self.end_date:%Y-%m-%d}"

    def includes(self, day: date) -> bool:
        return self.start_date <= day <= self.end_date

    def iter_dates(self):
        current = self.start_date
        while current <= self.end_date:
            yield current
            current += timedelta(days=1)


class WorkSchedule:
    def __init__(self, periods):
        self.periods = tuple(periods)
        self._validate()

    def find(self, day: date) -> WorkPeriod | None:
        return next((period for period in self.periods if period.includes(day)), None)

    def _validate(self):
        occupied_dates = {}
        for period in self.periods:
            if period.start_date > period.end_date:
                raise ValueError(f"工作期間起訖日期錯誤：{period.label}")
            if not period.goal.strip():
                raise ValueError(f"工作期間缺少工作目標：{period.label}")
            if not isinstance(period.hours, int) or period.hours <= 0:
                raise ValueError(f"每日工作時數需為正整數：{period.label}")

            for work_date in period.iter_dates():
                if work_date in occupied_dates:
                    previous = occupied_dates[work_date]
                    raise ValueError(
                        f"工作期間日期重疊：{work_date.isoformat()} "
                        f"同時存在於 {previous.label} 與 {period.label}"
                    )
                occupied_dates[work_date] = period


def work_period(year, month, start_day, end_day, goal, hours=8) -> WorkPeriod:
    return WorkPeriod(
        year=year,
        month=month,
        start_day=start_day,
        end_day=end_day,
        goal=goal,
        hours=hours,
    )


# 每個工作期間都有自己的工作目標與每日時數；同一期間內每日時數相同。
WORK_SCHEDULE = WorkSchedule([
    # 2026 年
    work_period(2026, 4, 6, 10, "閱讀既有程式碼與文件，釐清主要模組功能", hours=8),
    work_period(2026, 5, 4, 8, "實做徵才網雙語化，持續開發與測試，修正回報問題", hours=8),
    work_period(2026, 6, 8, 12, "為秋季國際生活動擴充功能、修復bug", hours=8),
    work_period(2026, 7, 6, 10, "部署架構、備份流程優化，建立統一管理介面", hours=8),
    work_period(2026, 8, 19, 21, "支援秋季國際生活動、協助解決問題", hours=8),
    work_period(2026, 8, 24, 28, "重構 Docker 部署、更新依賴套件", hours=8),
    work_period(2026, 9, 7, 11, "重構 Docker 部署、更新依賴套件", hours=8),
    work_period(2026, 9, 14, 17, "例行檢查並提升系統安全性", hours=5),
    work_period(2026, 10, 5, 9, "待補：十月第一組工作內容", hours=8),
    work_period(2026, 10, 12, 15, "待補：十月第二組工作內容", hours=5),
    work_period(2026, 11, 2, 6, "待補：十一月第一組工作內容", hours=8),
    work_period(2026, 11, 9, 12, "待補：十一月第二組工作內容", hours=5),
    work_period(2026, 12, 7, 11, "待補：十二月第一組工作內容", hours=8),
    work_period(2026, 12, 14, 17, "待補：十二月第二組工作內容", hours=5),

    # 2027 年工作期間可接續新增在這裡。
])
# ========= 模擬人類延遲 =========
async def human_delay(min_ms=500, max_ms=3000):
    delay = random.uniform(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)

# ======== 確認已進入人事管理系統 =========
async def ensure_in_target_url(page):
    while page.url != TARGET_URL:
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
    if page.url == TARGET_URL:
        print("➡️ 已進入人事系統頁面")
        await human_delay()

        await page.wait_for_selector("role=link[name='新增簽到']")
        await page.get_by_role("link", name="新增簽到").click()
        print("➡️ 已進入簽到頁面")
        await human_delay()
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
    if back_to_system_btn_exists:
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
async def run_automation(page, work_period):
    work_message = work_period.goal

    # 簽到流程
    await ensure_in_target_url(page)
    await human_delay()

    await page.wait_for_selector("role=button[name='更新時間']")
    await page.get_by_role("button", name="更新時間").click()
    print(f"🕐 更新時間：{datetime.now(TAIPEI_TZ).strftime('%H:%M:%S')}")
    await human_delay()
    
    await page.wait_for_selector("role=button[name='簽到']")
    await page.get_by_role("button", name="簽到").click()
    sign_in_time = datetime.now(TAIPEI_TZ)
    print(f"✅ 簽到：{sign_in_time.strftime('%H:%M:%S')}")
    await human_delay()

    wait_seconds = work_period.seconds + random.randint(0, SIGN_OUT_JITTER_SECONDS)
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
    print(f"🕐 更新時間：{datetime.now(TAIPEI_TZ).strftime('%H:%M:%S')}")
    await human_delay()
    
    await page.wait_for_selector("role=button[name='簽退']")
    await page.get_by_role("button", name="簽退").click()
    sign_out_time = datetime.now(TAIPEI_TZ)
    print(f"✅ 簽退：{sign_out_time.strftime('%H:%M:%S')}")
    await human_delay(3000, 5000)



# ========= 主流程 =========
async def main():
    now = datetime.now(TAIPEI_TZ)
    today = now.date()
    work_period = WORK_SCHEDULE.find(today)
    if work_period is None:
        print(f"🔕 今日日期 {today.isoformat()} 不在上班日期中，略過所有自動流程。")
        return

    print(f"📅 今日是 {today.isoformat()} 上班日，開始準備自動流程。")
    print(f"🗓️ 工作期間：{work_period.label}")
    print(f"⏳ 今日工作時數：{work_period.hours} 小時")
    print(f"📝 工作日誌內容：{work_period.goal}")


    # 等到上午 8:00–9:00 之間的隨機時間才執行第一步
    target = now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(seconds=random.randint(0, 3600))
    if now >= target:
        # 今天的時間窗口已過，等到明天
        target += timedelta(days=1)

    wait_seconds = (target - now).total_seconds()
    print(f"⏰ 目前時間：{now.strftime('%H:%M:%S')}，將於 {target.strftime('%m/%d %H:%M:%S')} 開始執行（等待 {wait_seconds/3600:.1f} 小時）")
    # await asyncio.sleep(wait_seconds)
    

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

        print(f"🚀 開始執行自動流程：{datetime.now(TAIPEI_TZ).strftime('%H:%M:%S')}")
        
        try:
            await run_automation(page, work_period)
            print("👌 自動簽到流程完成 (等待使用者確認後關閉)")
        except Exception as e:
            print("❌ 自動流程錯誤：", e)

        
        # input("按下 Enter 鍵結束程式...")

if __name__ == "__main__":
    asyncio.run(main())
