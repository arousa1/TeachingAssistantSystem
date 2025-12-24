import asyncio
import base64
import logging
import os
import sys
import shutil
import glob
import time
import cv2
import numpy as np
from browser_use import Agent, BrowserSession, Tools, ChatBrowserUse, BrowserProfile
from browser_use.agent.views import ActionResult
from playwright.async_api import Page, Frame, async_playwright
from pydantic import BaseModel, Field

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
LOG = logging.getLogger("RobotDebug")

def move_downloaded_files(target_dir: str, start_time: float, source_dir: str = None, timeout: int = 60):
    """
    移动自 start_time 之后在源目录中生成的所有文件到目标目录。

    :param target_dir: 目标文件夹路径
    :param start_time: 任务开始的时间戳 (time.time())
    :param source_dir: 浏览器默认下载目录 (默认自动获取)
    :param timeout: 等待下载完成的最大秒数
    """
    # 1. 确定源目录
    if not source_dir:
        source_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    print(f"📂 [文件处理] 正在扫描新文件... (时间阈值: {time.strftime('%H:%M:%S', time.localtime(start_time))})")

    # 确保目标目录存在
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    moved_count = 0
    wait_start = time.time()

    while True:
        # 获取源目录下所有文件
        all_files = glob.glob(os.path.join(source_dir, '*'))

        # 筛选出：任务开始后创建的 + 不是文件夹的文件
        new_files = []
        for f in all_files:
            try:
                # 注意：Windows下 getctime 是创建时间
                if os.path.isfile(f) and os.path.getctime(f) > start_time:
                    new_files.append(f)
            except Exception:
                continue  # 忽略无法读取的文件

        if not new_files:
            # 如果超时还没找到文件，退出
            if time.time() - wait_start > timeout:
                print("⚠️ [文件处理] 超时：未检测到任何新下载的文件。")
                break
            time.sleep(1)
            continue

        # 检查是否有文件正在下载 (以 .crdownload, .tmp, .part 结尾)
        downloading_files = [f for f in new_files if f.endswith(('.crdownload', '.tmp', '.part'))]

        if downloading_files:
            # 如果还有文件在下载，继续等待
            if time.time() - wait_start > timeout:
                print(f"⚠️ [文件处理] 等待下载完成超时，剩余未完成文件: {downloading_files}")
                break
            print(f"   ⏳ 正在下载 {len(downloading_files)} 个文件，等待完成...")
            time.sleep(2)
            continue

        # --- 所有文件均已就绪，开始移动 ---
        print(f"✅ 检测到 {len(new_files)} 个新文件，准备移动...")

        for file_path in new_files:
            filename = os.path.basename(file_path)
            target_path = os.path.join(target_dir, filename)

            # 处理重名：若目标存在同名文件，添加时间戳
            if os.path.exists(target_path):
                name, ext = os.path.splitext(filename)
                timestamp = int(time.time())
                target_path = os.path.join(target_dir, f"{name}_{timestamp}{ext}")

            try:
                shutil.move(file_path, target_path)
                print(f"   -> 已移动: {filename}")
                moved_count += 1
            except Exception as e:
                print(f"   ❌ 移动失败 {filename}: {e}")

        break  # 移动完成后退出循环

    print(f"🎉 [文件处理] 完成，共移动 {moved_count} 个文件。")
def move_latest_file_to_target(target_dir: str, source_dir: str = None, timeout: int = 30):
    """
    将源目录（默认为系统下载文件夹）中最新下载的文件移动到目标目录。

    :param target_dir: 最终文件要存放的目录
    :param source_dir: 浏览器默认下载路径 (如果不传，自动获取当前用户的 Downloads 目录)
    :param timeout: 等待文件下载完成的最大秒数
    """
    # 1. 确定源目录
    if not source_dir:
        # 自动获取系统默认下载路径 (Windows/Mac/Linux 通用)
        source_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    print(f"📂 [文件处理] 正在扫描源目录: {source_dir}")

    # 2. 循环检测最新文件
    start_time = time.time()
    target_file = None

    while time.time() - start_time < timeout:
        # 获取目录下所有文件
        list_of_files = glob.glob(os.path.join(source_dir, '*'))

        if not list_of_files:
            print("   ⏳ 目录为空，等待中...")
            time.sleep(1)
            continue

        # 按修改时间排序，获取最新的文件
        latest_file = max(list_of_files, key=os.path.getctime)
        filename = os.path.basename(latest_file)

        # 排除非文件类型（如文件夹）
        if not os.path.isfile(latest_file):
            continue

        # 3. 检查是否正在下载 (.crdownload 为 Chrome/Edge 临时后缀, .part 为 Firefox)
        if filename.endswith('.crdownload') or filename.endswith('.tmp') or filename.endswith('.part'):
            print(f"   ⏳ 文件正在下载中: {filename}，等待完成...")
            time.sleep(1)
            continue

        # 检查文件是否是最近生成的（防止移动了几天前的旧文件）
        # 这里设定为只移动最近 2 分钟内创建/修改的文件
        if time.time() - os.path.getctime(latest_file) > 120:
            print(f"   ⚠️ 发现的最新文件 [{filename}] 是旧文件，继续等待新下载...")
            time.sleep(1)
            continue

        target_file = latest_file
        break

    if not target_file:
        print("❌ [文件处理] 超时：未找到新下载的文件。")
        return

    # 4. 准备移动
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    target_path = os.path.join(target_dir, os.path.basename(target_file))

    # 5. 处理重名文件 (添加时间戳)
    if os.path.exists(target_path):
        name, ext = os.path.splitext(os.path.basename(target_file))
        timestamp = int(time.time())
        target_path = os.path.join(target_dir, f"{name}_{timestamp}{ext}")

    try:
        # 使用 shutil.move 移动文件
        shutil.move(target_file, target_path)
        print(f"✅ [文件处理] 成功将文件移动到: {target_path}")
    except Exception as e:
        print(f"❌ [文件处理] 移动失败: {e}")

# ================= 配置区域 =================
# 下载路径 (确保路径存在)
DOWNLOAD_DIR = 'D:/Code/Python/西电资料'
# 指定一个用于存放浏览器缓存和用户数据的目录
USER_DATA_DIR = 'D:/Code/Python/UserData/browser_data'


# ================= 全局变量 (用于旁路连接) =================
side_playwright = None
side_browser = None
side_context = None
# ================= 核心修复：系统提示词 =================
extend_system_message = """
# 核心指令：验证码处理与文件下载

## 1. 验证码处理 (最高优先级)
- 遇到滑块/拼图验证时，**必须**调用 `[playwright_slider_verification]`。
"""


class PlaywrightSliderAction(BaseModel):
    timeout: int = Field(default=10000, description='Timeout for waiting for slider elements')


# ================= 辅助函数 =================
async def get_base64_img(target: Page | Frame, selector: str) -> np.ndarray:
    src = await target.locator(selector).get_attribute('src')
    if not src or ',' not in src:
        raise ValueError(f'{selector} 没有 base64 数据')
    header, data = src.split(',', 1)
    img_bytes = base64.b64decode(data)
    img_np = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(img_np, cv2.IMREAD_COLOR)


class SliderSolver:
    @staticmethod
    def identify_gap(bg_img: np.ndarray, slider_img: np.ndarray) -> float:
        bg_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)
        slider_gray = cv2.cvtColor(slider_img, cv2.COLOR_BGR2GRAY)
        bg_edge = cv2.Canny(bg_gray, 100, 200)
        slider_edge = cv2.Canny(slider_gray, 100, 200)
        result = cv2.matchTemplate(bg_edge, slider_edge, cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(result)
        return float(max_loc[0])


tools = Tools()


# ================= 工具定义 =================
async def init_side_playwright(cdp_url: str):
    """
    连接到 browser-use 已经打开的浏览器
    """
    global side_playwright, side_browser, side_context
    try:
        if side_context:
            return side_context

        LOG.info(f"🔌 正在建立 Playwright 旁路连接 (CDP: {cdp_url})...")
        side_playwright = await async_playwright().start()
        # 连接到现有的 CDP
        side_browser = await side_playwright.chromium.connect_over_cdp(cdp_url)

        # 获取上下文
        if side_browser.contexts:
            side_context = side_browser.contexts[0]
        else:
            side_context = await side_browser.new_context()

        LOG.info("✅ 旁路连接建立成功，已获取 Context，")
        return side_context
    except Exception as e:
        LOG.error(f"❌ 建立旁路连接失败: {e}")
        return None


async def get_latest_page_from_side_context():
    """从旁路 Context 中获取最新活动的页面"""
    if not side_context:
        return None

    # 简单的策略：找最后一个未关闭的页面
    pages = [p for p in side_context.pages if not p.is_closed()]
    if pages:
        return pages[-1]
    return None


@tools.registry.action(
    "Solve the slider verification code.",
    param_model=PlaywrightSliderAction,
)
async def playwright_slider_verification(params: PlaywrightSliderAction):
    LOG.info("🔍 开始滑块验证...")

    # 【修复】使用旁路连接获取 Page
    page = await get_latest_page_from_side_context()

    if not page:
        return ActionResult(error="❌ 无法通过旁路连接获取页面。请确保 Side-Channel 已初始化。")

    try:
        # 这里拿到的 page 是标准的 Playwright 对象，拥有所有方法
        await page.wait_for_load_state("domcontentloaded", timeout=10000)

        target_page = page
        offset_x, offset_y = 0, 0

        # 查找 iframe 逻辑
        for frame in page.frames:
            if await frame.locator('.slider').count() > 0:
                target_page = frame
                try:
                    frame_elem = await page.locator(f'iframe[src*="{frame.url.split("/")[-1]}"]').first
                    if await frame_elem.count() == 0:
                        frame_elem = page.locator('iframe').first
                    if await frame_elem.count() > 0:
                        box = await frame_elem.bounding_box()
                        if box:
                            offset_x, offset_y = box['x'], box['y']
                except:
                    pass
                break

        await target_page.wait_for_selector('.slider', state='attached', timeout=5000)
        bg_img = await get_base64_img(target_page, '#slider-img1')
        piece_img = await get_base64_img(target_page, '#slider-img2')
        gap = SliderSolver.identify_gap(bg_img, piece_img)

        bg_w = bg_img.shape[1]
        canvas_box = await target_page.locator('canvas.block').first.bounding_box()
        ratio = 1.0
        if canvas_box and bg_w > 0:
            ratio = canvas_box['width'] / bg_w

        drag_distance = gap * ratio
        LOG.info(f"🎯 缺口: {gap}, 缩放比: {ratio:.2f}, 拖动: {drag_distance:.2f}")

        slider_btn = target_page.locator('div.slider').first
        btn_box = await slider_btn.bounding_box()

        if not btn_box:
            return ActionResult(error="❌ 无法获取滑块坐标")

        start_x = offset_x + btn_box['x'] + btn_box['width'] / 2
        start_y = offset_y + btn_box['y'] + btn_box['height'] / 2

        await page.mouse.move(start_x, start_y)
        await page.mouse.down()
        await page.mouse.move(start_x + drag_distance, start_y, steps=30)
        await asyncio.sleep(0.5)
        await page.mouse.up()

        await asyncio.sleep(3)
        if await target_page.locator("text=向右滑动").count() == 0:
            return ActionResult(extracted_content=f'✅ Slider solved!')
        else:
            return ActionResult(error="❌ 验证失败，请重试")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return ActionResult(error=f"Slider error: {str(e)}")

    finally:
        # 取消playwright连接，防止影响下载功能
        global side_playwright, side_browser, side_context
        try:
            # 1. 关闭上下文
            if side_context:
                await side_context.close()

            # 2. 断开浏览器 CDP 连接 (注意：connect_over_cdp 的 close 通常只是断开连接，不会关闭实际浏览器)
            if side_browser:
                await side_browser.close()

            # 3. 停止 Playwright 驱动
            if side_playwright:
                await side_playwright.stop()

            LOG.info("🔌 旁路 Playwright 连接已断开，控制权归还主程序")
        except Exception as disconnect_err:
            LOG.error(f"⚠️ 断开旁路连接时发生非致命错误: {disconnect_err}")
        finally:
            # 确保全局变量重置，方便下次重新连接
            side_context = None
            side_browser = None
            side_playwright = None

        global browser_session
        browser_session.BrowserProfile.downloads_path = DOWNLOAD_DIR


async def test():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    profile = BrowserProfile(
        headless=False,
        downloads_path=DOWNLOAD_DIR,
        # user_data_dir=USER_DATA_DIR
    )

    browser_session = BrowserSession(browser_profile=profile)
    llm = ChatBrowserUse()  # 建议显式指定模型，如 ChatOpenAI(model='gpt-4o')


    # 1. 启动 Session
    await browser_session.start()



    # 【修复步骤 2】等待 Session 稳定
    # browser-use 启动浏览器后可能还在进行一些内部初始化，稍微等一下能避免死锁
    await asyncio.sleep(10)

    # 我们利用 session 暴露的 CDP URL 自己连上去
    if hasattr(browser_session, 'cdp_url') and browser_session.cdp_url:
        await init_side_playwright(browser_session.cdp_url)
    else:
        LOG.error("❌ BrowserSession 没有提供 cdp_url，无法建立连接！")


    # 定义任务
    task_prompt = """
        1. 打开 https://xdspoc.xidian.edu.cn/ 
        2. 【登录流程】：
           - 如果页面显示存在用户登录按钮则表示未登录，点击用户登录，账号: 24031212124, 密码: lww496177401。
           - 如果已经登录（直接进入了系统），则**跳过登录步骤**，直接进行下一步。
           - 若出现滑块验证，必须调用工具 [playwright_slider_verification]。
        3. 导航操作：点击 "个人空间" -> "组合数学" -> "资料" -> "新建文件夹"。
        4. 【下载操作】：
           - 识别文件列表。
           - 勾选所有文件，点击"批量下载"（或者逐个下载）。
           - **重要**：点击下载后，请等待至少 5 秒，不要急着结束任务，等待文件保存。
        说明：
           - 若操作过程中出现了统一认证页面，则先进行登录流程
        """

    agent = Agent(
        task=task_prompt,
        llm=llm,
        use_vision=True,
        extend_system_message=extend_system_message,
        browser_session=browser_session,
        tools=tools
    )

    try:
        LOG.info("🤖 智能体开始运行...")
        # ==========================================
        # 1. 【关键】记录任务开始时间
        # ==========================================
        task_start_time = time.time()
        await agent.run()

        LOG.info("⏳ 任务结束，额外等待 10 秒以确保最后的文件写入完成...")
        await asyncio.sleep(10)

        LOG.info("📦 任务执行完毕，等待文件落盘并移动...")

        # 2. 给一点缓冲时间，确保下载请求已经发起了
        await asyncio.sleep(5)

        # ==========================================
        # 3. 【关键】调用批量移动函数
        # ==========================================
        move_downloaded_files(
            target_dir=DOWNLOAD_DIR,
            start_time=task_start_time,
            timeout=120  # 如果文件很大或很多，适当增加超时时间(秒)
        )

    finally:
        LOG.info("🔒 关闭浏览器会话")
        await browser_session.close()


if __name__ == "__main__":
    asyncio.run(test())