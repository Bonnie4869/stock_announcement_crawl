from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import logging
import os
import time
import random


class DriverController:
    def __init__(
        self,
        driver: webdriver.Chrome = None,
        download_dir: str = None,
        logger: logging.Logger = None,
    ):
        self.driver = driver
        self.logger = logger or self._setup_default_logger()
        self.download_dir = (
            download_dir or "cninfo_file/announcements"
        )  # default settings
        os.makedirs(self.download_dir, exist_ok=True)
        self._is_self_managed_driver = False

    def _setup_default_logger(self) -> logging.Logger:
        """
        - 创建默认日志记录器
        - 输入：无
        - 输出：配置好的日志记录器实例
        """
        logger = logging.getLogger("DriverController")
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

    def start_browser(self, headless: bool = False) -> None:
        """
        - 启动浏览器
        - 输入：
            - headless: 是否无界面运行
            - download_dir: 文件下载存储路径
        - 输出：无
        """
        download_dir = self.download_dir
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
        if not self.driver:
            return ""

        try:
            os.makedirs("screenshots", exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshots/{prefix}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            self.logger.info(f"截图已保存: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"截图失败: {str(e)}")
            return ""

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
