from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import re
import logging
import datetime
from datetime import datetime
from typing import Tuple
import random
import os
from urllib.parse import urljoin
from db_save import AnnouncementDB


class AnnouncementDownloadController:
    """
    AnnouncementDownloadController - 用于控制网页日期选择器交互及数据抓取的类

    属性：
        driver (webdriver.Chrome): Selenium浏览器驱动实例
        logger (logging.Logger): 日志记录器
        _is_self_managed_driver (bool): 标记是否由本实例创建的驱动,只操作由该实体创建的driver
        downloader: 用于公告文件下载
    """

    def __init__(self, driver: webdriver.Chrome = None, logger: logging.Logger = None):
        """
        - 初始化driver
        - 输入：
            - driver: 可选的现有浏览器驱动实例
            - logger: 可指定的自定义日志记录器
        - 输出：无
        """
        self.driver = driver
        self.logger = logger or self._setup_default_logger()
        self._is_self_managed_driver = False

    def _setup_default_logger(self) -> logging.Logger:
        """
        - 创建默认日志记录器
        - 输入：无
        - 输出：配置好的日志记录器实例
        """
        logger = logging.getLogger("AnnouncementDownloadController")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _setup_driver_options(
        self, download_dir: str, headless: bool = False
    ) -> webdriver.ChromeOptions:
        """
        - 配置浏览器选项
        - 输入：
            - download_dir: 文件下载目录
            - headless: 是否无头模式运行
        - 输出：配置好的浏览器选项
        """
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        prefs = {
            "download.default_directory": os.path.abspath(download_dir),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
        }
        options.add_experimental_option("prefs", prefs)
        return options

    def start_browser(
        self, headless: bool = False, download_dir: str = "data/announcements"
    ) -> None:
        """
        - 启动浏览器
        - 输入：
            - headless: 是否无界面运行
            - download_dir: 文件下载存储路径
        - 输出：无
        """
        if self.driver is not None:
            self.logger.warning("Browser already initialized")
            return
        options = self._setup_driver_options(
            download_dir=download_dir, headless=headless
        )
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.maximize_window()
            self._is_self_managed_driver = True
            self.logger.info(
                f"Browser started with download path: {os.path.abspath(download_dir)}"
            )
        except Exception as e:
            self.logger.error(f"Failed to start browser: {str(e)}")
            raise

    def open_date_picker(
        self,
        url: str,
        trigger_locator: Tuple[str, str] = (
            By.CSS_SELECTOR,
            "span.range_date.js_laydateSearch[lay-key='1']",
        ),
        picker_locator: Tuple[str, str] = (By.CSS_SELECTOR, ".layui-laydate"),
        timeout: int = 15,
    ) -> bool:
        """
         - 打开目标页面的日期选择器
        - 输入：
            - url: 目标网页地址
            - trigger_locator: 日期选择器触发元素定位器
            - picker_locator: 定位打开后的日期选择器，作为自动化测试用例的检查点，可视化检查操作流程
            - timeout: 最大等待时间(秒)
        - 输出：成功返回True，失败返回False
        """
        if self.driver is None:
            self.start_browser()

        try:
            self.driver.get(url)
            self.logger.info(f"Navigated to: {url}")
            trigger = self._wait_and_highlight(
                *trigger_locator, timeout=timeout, highlight_color="red"
            )
            self._reliable_click(trigger)
            self._wait_and_highlight(
                *picker_locator, timeout=timeout, highlight_color="blue"
            )  # 高亮展示日期选择器位置
            return True
        except Exception as e:
            self.logger.error(f"Failed to open date picker: {str(e)}")
            self._take_screenshot("date_picker_error")
            return False

    """
    6. minus_year_cliker(by: str, locator: str) -> None
    - 点击年份减按钮
    - 输入：
        - by: 元素定位方式
        - locator: 元素定位表达式
    - 输出：无

    7. plus_year_cliker(by: str, locator: str) -> None
    - 点击年份加按钮
    - 输入/输出：同minus_year_cliker

    8. minus_month_cliker(by: str, locator: str) -> None
    - 点击月份减按钮
    - 输入/输出：同minus_year_cliker

    9. plus_month_cliker(by: str, locator: str) -> None
    - 点击月份加按钮
    - 输入/输出：同minus_year_cliker
    """

    def minus_year_cliker(self, by: str, locator: str):
        self._reliable_click(self._wait_and_highlight(by, locator))

    def plus_year_cliker(self, by: str, locator: str):
        self._reliable_click(self._wait_and_highlight(by, locator))

    def minus_month_cliker(self, by: str, locator: str):
        self._reliable_click(self._wait_and_highlight(by, locator))

    def plus_month_cliker(self, by: str, locator: str):
        self._reliable_click(self._wait_and_highlight(by, locator))

    """
    10. operate_start_year_box(offset: int) -> None
    - 调整起始年份
    - 输入：
        - offset: 调整年数(正数增加/负数减少)
    - 输出：无

    11. operate_start_month_box(offset: int) -> None
    - 调整起始月份
    - 输入：
        - offset: 调整月数(正数增加/负数减少)
    - 输出：无

    12. operate_end_year_box(offset: int) -> None
    - 调整结束年份
    - 输入：
        - offset: 调整年数(正数增加/负数减少)
    - 输出：无

    13. operate_end_month_box(offset: int) -> None
    - 调整结束月份
    - 输入：
        - offset: 调整月数(正数增加/负数减少)
    - 输出：无
    """

    def operate_start_year_box(self, offset):
        self._operate_year(offset, 0)

    def operate_start_month_box(self, offset):
        self._operate_month(offset, 0)

    def operate_end_year_box(self, offset):
        self._operate_year(offset, 1)

    def operate_end_month_box(self, offset):
        self._operate_month(offset, 1)

    def _operate_year(self, offset, panel):
        """
        - 内部方法：操作年份调整
        - offset: 调整幅度
        - panel: 面板索引(0开始/1结束)
        """
        action = self.minus_year_cliker if offset < 0 else self.plus_year_cliker
        for _ in range(abs(offset)):
            action(
                By.CSS_SELECTOR,
                f".laydate-main-list-{panel} .laydate-{'prev' if offset < 0 else 'next'}-y",
            )

    def _operate_month(self, offset, panel):
        """
        - 内部方法：操作月份调整
        - offset: 调整幅度
        - panel: 面板索引(0开始/1结束)
        """
        action = self.minus_month_cliker if offset < 0 else self.plus_month_cliker
        for _ in range(abs(offset)):
            action(
                By.CSS_SELECTOR,
                f".laydate-main-list-{panel} .laydate-{'prev' if offset < 0 else 'next'}-m",
            )

    """
        - 组合日期为YYYY-MM-DD格式字符串
    - 输入：
      - y: 年
      - m: 月
      - d: 日
    - 输出：格式化后的日期字符串
    """

    def compose_date(self, y, m, d):
        return f"{y}-{m}-{d}"

    def select_date(self, start_date, end_date):
        """
        - 在日期选择器中选择日期范围
        - 输入：
        - start_date: 开始日期(YYYY-MM-DD)
        - end_date: 结束日期(YYYY-MM-DD)
        - 输出：成功返回True，失败返回False
        """
        try:
            # s_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            # e_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            s_date = start_date
            e_date = end_date

            s_loc = self._wait_and_highlight(
                By.CSS_SELECTOR, ".laydate-main-list-0 .laydate-set-ym"
            )
            s_y, s_m = map(int, re.findall(r"\d+", s_loc.text))
            self.operate_start_year_box(s_date.year - s_y)
            self.operate_start_month_box(s_date.month - s_m)

            e_loc = self._wait_and_highlight(
                By.CSS_SELECTOR, ".laydate-main-list-1 .laydate-set-ym"
            )
            e_y, e_m = map(int, re.findall(r"\d+", e_loc.text))
            self.operate_end_year_box(e_date.year - e_y)
            self.operate_end_month_box(e_date.month - e_m)

            start_selector = f'.laydate-main-list-0 td[lay-ymd="{self.compose_date(s_date.year, s_date.month, s_date.day)}"]'
            end_selector = f'.laydate-main-list-1 td[lay-ymd="{self.compose_date(e_date.year, e_date.month, e_date.day)}"]'
            self._reliable_click(
                self._wait_and_highlight(By.CSS_SELECTOR, start_selector)
            )
            self._reliable_click(
                self._wait_and_highlight(By.CSS_SELECTOR, end_selector)
            )
            time.sleep(random.randint(1, 3))
        except Exception as e:
            self.logger.error(f"Failed to select date: {str(e)}")
            self._take_screenshot("select_date_error")
            return False

    def confirm(self):
        """
        - 确认日期选择
        - 输入：无
        - 输出：无
        """
        self._reliable_click(
            self._wait_and_highlight(By.CSS_SELECTOR, "span.laydate-btns-confirm")
        )
        time.sleep(random.randint(1, 2))

    def data_statistics(self):
        """
        - 显示数据统计结果(数据总共条数)
        - 输入：无
        - 输出：无(打印到控制台)
        """
        total = self._wait_and_highlight(By.CSS_SELECTOR, "span.bulletinNum").text
        total = int(total.strip("条"))
        print(f"Total search result(总公告数): {total}")
        return total

    def create_url(self, url):
        """
        - 构建完整URL
        - 输入：
        - url: 相对或绝对URL
        - 输出：完整的绝对URL
        """
        return (
            urljoin("https://www.sse.com.cn", url)
            if not url.startswith("http")
            else url
        )

    def download_file_function(self, url, save_dir, filename, max_attempt=3):
        """
        - 下载文件
        - 输入：
        - url: 文件URL
        - save_dir: 保存目录
        - filename: 目标文件名
        - max_attempt: 最大尝试次数
        - 输出：下载成功返回True，否则False
        """
        save_path = os.path.join(save_dir, filename)
        os.makedirs(save_dir, exist_ok=True)

        # 检查文件是否已存在
        if os.path.exists(save_path):
            file_size = os.path.getsize(save_path)
            if file_size > 0:  # 确保不是空文件
                self.logger.info(
                    f"文件已存在，跳过下载: {filename} (大小: {file_size/1024:.2f}KB)"
                )
                return False

        # 记录当前页面状态
        original_window = self.driver.current_window_handle

        # 在新标签页打开
        self.driver.switch_to.new_window("tab")

        for attempt in range(max_attempt):
            try:
                # 记录下载前的文件状态
                original_files = set(
                    f
                    for f in os.listdir(save_dir)
                    if os.path.isfile(os.path.join(save_dir, f))
                )

                # 访问下载链接
                self.driver.get(url)
                self.logger.info(
                    f"Downloading: Target={filename} (Attempt {attempt+1}/{max_attempt})"
                )

                # 监控下载进度
                downloaded_file = None
                for _ in range(60):  # 最多等待30秒
                    time.sleep(0.5)  # 控制间隔时间
                    # current_file 排除新文件
                    current_files = set(
                        f
                        for f in os.listdir(save_dir)
                        if os.path.isfile(os.path.join(save_dir, f))
                        and not f.endswith(".crdownload")  # 核心修复点
                    )
                    new_files = current_files - original_files

                    # 检查新文件
                    if new_files:
                        # 查看最新修改的文件
                        newest_file = max(
                            new_files,
                            key=lambda f: os.path.getmtime(os.path.join(save_dir, f)),
                        )
                        temp_path = os.path.join(save_dir, newest_file)

                        # 检查文件是否完整（大小稳定）
                        size1 = os.path.getsize(temp_path)
                        time.sleep(random.uniform(0.5, 1.0))
                        size2 = os.path.getsize(temp_path)

                        if size1 == size2 and size1 > 0:
                            downloaded_file = temp_path
                            break

                if downloaded_file:
                    try:
                        # 重命名文件
                        os.rename(downloaded_file, save_path)
                        self.logger.info(
                            f"Download completed and renamed to: {filename}"
                        )
                        # 关闭标签页并返回
                        self.driver.close()
                        self.driver.switch_to.window(original_window)
                        return True
                    except Exception as e:
                        self.logger.error(f"Rename failed: {e}")
                        continue

                self.logger.warning(
                    f"Attempt {attempt+1} failed - No valid download detected"
                )

            except Exception as e:
                self.logger.error(
                    f"Download attempt {attempt+1} failed with error: {str(e)}"
                )
                self._take_screenshot("download_error")
                # 即使出错也尝试返回原始页面
                try:
                    # 关闭标签页并返回
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
                except:
                    pass
                time.sleep(2)

        # 关闭标签页并返回
        self.driver.close()
        self.driver.switch_to.window(original_window)
        return False

    def data_crawler(
        self,
        total_cnt,
        max_bulletin_num=100,
        max_page=10000,
        download_files=True,
        save_dir="data/announcements",
    ):
        """
        - 抓取公告数据
        - 输入：
        - max_bulletin_num: 最大下载公告数
        - max_page: 最大处理页数
        - download_files: 是否下载文件
        - save_dir: 文件保存目录
        - 输出：无(数据存入数据库)
        """
        db = AnnouncementDB("data/announcements.db")
        current_page = 1
        download_cnt = 0
        failures = 0

        while (
            current_page <= max_page
            and download_cnt < max_bulletin_num
            and failures < 5
            and download_cnt < total_cnt
        ):
            print(f"current page: {current_page}")
            try:
                table = self._wait_and_highlight(By.CSS_SELECTOR, "table.table-hover")
                rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")

                # 处理一个stock有多个公告的情况
                current_code = ""
                current_name = ""

                for row in rows:
                    if download_cnt % 10 == 0:
                        self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
                        self.driver.execute_cdp_cmd(
                            "Storage.clearDataForOrigin",
                            {"origin": "*", "storageTypes": "all"},
                        )

                    if (
                        download_cnt >= total_cnt
                        or download_cnt >= max_bulletin_num
                        or failures >= 5
                    ):
                        break

                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) < 6:
                            continue

                        code = cells[0].text.strip()
                        name = cells[1].text.strip()

                        if code == "" or name == "":
                            code = current_code
                            name = current_name
                        else:
                            current_code = code
                            current_name = name

                        title = cells[2].text.strip()
                        link = (
                            cells[2]
                            .find_element(By.TAG_NAME, "a")
                            .get_attribute("href")
                        )
                        type = cells[4].text.strip()
                        date = cells[5].text.strip()
                        url = self.create_url(link)

                        record = {
                            "stock_code": code,
                            "stock_name": name,
                            "announcement_title": title,
                            "announcement_type": type,
                            "announcement_date": date,
                            "announcement_url": url,
                        }

                        if download_files and url and not db.record_exists(url):
                            try:
                                # Clean filename
                                clean_title = re.sub(r'[\\/*?:"<>|]', "", title)[
                                    :50
                                ]  # Limit length
                                file_name = f"{code}_{date}_{clean_title}.pdf"

                                # download start
                                success = self.download_file_function(
                                    url=url,
                                    save_dir=save_dir,
                                    filename=file_name,
                                    max_attempt=3,
                                )
                                if success:
                                    file_info = {
                                        "file_name": file_name,
                                        "file_path": os.path.join(save_dir, file_name),
                                    }
                                    db.save_record(record, file_info)
                                    download_cnt += 1
                                    failures = 0
                                    continue
                                time.sleep(
                                    random.randint(1, 3)
                                )  # Delay between downloads

                            except Exception as e:
                                failures += 1
                                self.logger.error(f"Download error: {str(e)}")

                    except Exception as e:
                        failures += 1
                        self.logger.warning(f"Row processing error: {str(e)}")
                        continue

                    time.sleep(3)

                current_page += 1
                if (
                    download_cnt < max_bulletin_num
                    and failures < 5
                    and download_cnt < total_cnt
                ):
                    try:
                        next_btn = self._wait_and_highlight(
                            By.CSS_SELECTOR, "li.next a"
                        )
                        if "disabled" in next_btn.get_attribute("class"):
                            self.logger.info("已经是最后一页，无法继续翻页")
                            return False
                        self._reliable_click(next_btn)
                        time.sleep(random.uniform(1, 3))
                    except:
                        print("翻页失败")
                        break  # No more pages

            except Exception as e:
                self.logger.error(f"Page processing error: {str(e)}")
                break
        print(f"total crawler announcement count: {download_cnt}")
        self.logger.info(
            f"Finished. Downloaded {download_cnt} files. Failures: {failures}"
        )

    def _wait_and_highlight(
        self, by: str, locator: str, timeout: int = 10, highlight_color: str = "red"
    ):
        """
        - 等待并高亮元素
        - 输入：
        - by: 定位策略
        - locator: 元素定位表达式
        - timeout: 最大等待时间
        - highlight_color: 高亮颜色
        - 输出：找到的页面元素
        """
        context = self.driver
        element = WebDriverWait(context, timeout).until(
            EC.presence_of_element_located((by, locator))
        )
        self.driver.execute_script(
            f"arguments[0].style.border='3px solid {highlight_color}';", element
        )
        time.sleep(random.uniform(0.5, 1.0))
        return element

    def _reliable_click(self, element):
        """
        - 可靠点击元素
        - 输入：
        - element: 要点击的页面元素
        - 输出：无
        """
        try:
            element.click()
        except:
            try:
                ActionChains(self.driver).move_to_element(element).pause(
                    random.uniform(0.5, 1.0)
                ).click().perform()
            except:
                self.driver.execute_script("arguments[0].click();", element)

    def _take_screenshot(self, prefix="error"):
        """
        - 截取当前页面截图
        - 输入：
        - prefix: 截图文件名前缀
        - 输出：无(保存截图文件)
        """
        if self.driver:
            ts = time.strftime("%Y%m%d_%H%M%S")
            path = f"{prefix}_{ts}.png"
            self.driver.save_screenshot(path)
            self.logger.info(f"Screenshot saved: {path}")

    def close(self):
        """
        - 关闭浏览器并清理
        - 输入：无
        - 输出：无
        """
        if self.driver and self._is_self_managed_driver:
            self.driver.quit()
            self.logger.info("Browser closed")
        self.driver = None


from dateutil.relativedelta import relativedelta


def get_date_input():
    """
    功能流程：
        1. 循环提示用户输入开始/结束日期
        2. 验证日期格式有效性
        3. 检查日期范围合理性
        4. 确保间隔不超过3个月

    返回:
        tuple (start_date, end_date) - 通过验证的datetime.date对象
    """
    while True:
        start_date_str = input(
            "请输入爬取开始日期(格式：YYYY-MM-DD，例如'2025-07-02'): "
        )
        end_date_str = input("请输入爬取结束日期(格式：YYYY-MM-DD，例如'2025-07-03'): ")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date < start_date:
                print("错误：结束日期不能早于开始日期")
                continue

            # 精确计算三个月的间隔
            three_months_later = start_date + relativedelta(months=3)

            if end_date > three_months_later:
                print("错误：日期间隔不能超过三个月")
            else:
                return start_date, end_date

        except ValueError:
            print("错误：日期格式不正确，请使用YYYY-MM-DD格式")


def main():
    """
    公告下载自动化流程控制器

    功能流程：
    1. 获取用户输入的时间范围
    2. 初始化浏览器控制器
    3. 打开目标网页并操作日期选择器
    4. 执行数据爬取和下载
    5. 确保资源清理

    用法示例：
    >>> main()
    请输入爬取开始日期(格式：YYYY-MM-DD，例如'2025-07-02'): 2025-07-01
    请输入爬取结束日期(格式：YYYY-MM-DD，例如'2025-07-03'): 2025-07-03
    [系统自动执行后续操作...]
    """

    start_date, end_date = get_date_input()
    """
    start_date: datetime.date对象，用户输入的起始日期
    end_date: datetime.date对象，用户输入的结束日期
    注意：日期范围不能超过3个月，通过get_date_input()内部验证
    """

    max_announcement_cnt = int(input("请输入你想要获取的最大公告条数(default = 100): "))
    print("程序启动...")

    controller = AnnouncementDownloadController()
    try:
        controller.start_browser(headless=False, download_dir="data/announcements")
        if controller.open_date_picker(
            "https://www.sse.com.cn/disclosure/listedinfo/announcement/"
        ):
            controller.select_date(start_date, end_date)
            controller.confirm()
            total_cnt = controller.data_statistics()
            controller.data_crawler(total_cnt, max_announcement_cnt)
    finally:
        controller.close()


if __name__ == "__main__":
    main()
