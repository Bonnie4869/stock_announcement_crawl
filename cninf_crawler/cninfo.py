import requests
import json
import time
import random
from cninfo_db import CninfoAnnouncementDB
from driverController import DriverController
import os
from selenium.webdriver.common.by import By


class Cninfo:
    # default settings
    """
    默认Headers设置
    """
    DEFAULT_HEADERS = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host": "www.cninfo.com.cn",
        "Origin": "https://www.cninfo.com.cn",
        "Referer": "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": "JSESSIONID=; insert_cookie=",
    }
    """
    默认爬取url
    """
    QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"

    def __init__(self):
        """
        Cninfo类初始化
        db: 初始化/提取文件路径下 公告存储数据库
        searchKey: 初始化公告下载关键词 - 用于灵活搜索
        plate: 初始化公告下载筛选板块 - 用于灵活搜索
        """
        self.db = CninfoAnnouncementDB("cninfo_file/announcements.db")
        self.searchKey = ""
        self.plate = ""

    def edit_payload(self, searchKey, plate):
        """
        设置搜索关键词和板块

        参数:
            searchKey (str): 公告搜索关键词
            plate (str): 股票市场板块代码
        """
        self.searchKey = searchKey
        self.plate = plate

    def query_get(self, start_date, end_date):
        """
        查询指定日期范围内的公告总页数

        参数:
            start_date (str): 开始日期(YYYY-MM-DD格式)
            end_date (str): 结束日期(YYYY-MM-DD格式)

        返回:
            int: 总页数，查询失败返回None
        """
        # payload
        payload = {
            "pageNum": "1",
            "pageSize": "30",
            "column": "szse",
            "tabName": "fulltext",
            "plate": self.plate,  # "",
            "stock": "",
            "searchkey": self.searchKey,  # "",
            "secid": "",
            "category": "",
            "trade": "",
            "seDate": f"{start_date}~{end_date}",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }

        response = requests.post(
            url=self.QUERY_URL, headers=self.DEFAULT_HEADERS, data=payload
        )

        if response.status_code == 200:
            data = response.text
            data = json.loads(data)
            total_record = data["totalRecordNum"]
            total_announcement = data["totalAnnouncement"]
            total_page = data["totalpages"]
            print(f"total records: {total_record}")
            print(f"total announcements: {total_announcement}")
            print(f"total pages: {total_page}")
            return total_page
        else:
            print(f"请求失败，状态码：{response.status_code}")
            return None

    def query_record(self, date):
        """
        查询指定日期的公告总数

        参数:
            date (str): 查询日期(YYYY-MM-DD格式)

        返回:
            int: 公告总数，查询失败返回None
        """
        # payload
        payload = {
            "pageNum": "1",
            "pageSize": "30",
            "column": "szse",
            "tabName": "fulltext",
            "plate": "",
            "stock": "",
            "searchkey": "",
            "secid": "",
            "category": "",
            "trade": "",
            "seDate": f"{date}~{date}",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }

        response = requests.post(
            url=self.QUERY_URL, headers=self.DEFAULT_HEADERS, data=payload
        )

        if response.status_code == 200:
            data = response.text
            data = json.loads(data)
            total_record = data["totalRecordNum"]
            total_announcement = data["totalAnnouncement"]
            total_page = data["totalpages"]
            print(f"total records: {total_record}")
            print(f"total announcements: {total_announcement}")
            print(f"total pages: {total_page}")
            return total_record
        else:
            print(f"请求失败，状态码：{response.status_code}")
            return None

    def query_all(self, start_date, end_date, total_page, max_save_cnt=100, max_fail=5):
        """
        下载指定日期范围内的所有公告

        参数:
            start_date (str): 开始日期(YYYY-MM-DD格式)
            end_date (str): 结束日期(YYYY-MM-DD格式)
            total_page (int): 总页数
            max_save_cnt (int): 最大保存文件数，默认100
            max_fail (int): 最大失败次数，默认5
        """
        # payload
        total_save_cnt = 0
        total_fail_cnt = 0
        # for i in range(1, 2):
        for i in range(1, total_page + 1):
            if total_fail_cnt >= max_fail:
                print("program has failed to much")
                break
            if total_save_cnt >= max_save_cnt:
                print(f"program have save enough files: {total_save_cnt} files")
            time.sleep(random.randint(1, 2))
            payload = {
                "pageNum": f"{i}",
                "pageSize": "30",
                "column": "szse",
                "tabName": "fulltext",
                "plate": self.plate,  # "",
                "stock": "",
                "searchkey": self.searchKey,  # "",
                "secid": "",
                "secid": "",
                "category": "",
                "trade": "",
                "seDate": f"{start_date}~{end_date}",
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true",
            }

            response = requests.post(
                url=self.QUERY_URL, headers=self.DEFAULT_HEADERS, data=payload
            )

            if response.status_code == 200:
                data = response.text
                data = json.loads(data)
                success, page_save_cnt = self.save_page(
                    data,
                )
                total_save_cnt += page_save_cnt
                if success == False:
                    total_fail_cnt += 1
                print(f"page {i} have download {page_save_cnt} files")

        print(f"total download files cnt: {total_save_cnt}")

    def query(self, start_date, end_date):
        """
        查询并下载指定日期范围内的公告

        参数:
            start_date (str): 开始日期(YYYY-MM-DD格式)
            end_date (str): 结束日期(YYYY-MM-DD格式)
        """
        total_page = self.query_get(start_date, end_date)
        if total_page > 0:
            self.query_all(start_date, end_date, total_page)
        else:
            print("no data has found")

    def save_file(
        self,
        url,
        download_dir="cninfo_file/announcements",
        max_attempt=3,
    ):
        """
        下载单个公告文件

        参数:
            url (str): 公告下载URL
            download_dir (str): 文件下载目录，默认"cninfo_file/announcements"
            max_attempt (int): 最大尝试次数，默认3

        返回:
            bool: 下载是否成功
        """
        dc = None
        download_status = False
        try:
            dc = DriverController(download_dir=download_dir)
            if not dc.driver:  # 确保浏览器未初始化
                dc.start_browser()
            dc.driver.get(url)

            save_dir = download_dir
            # attempt
            for attempt in range(max_attempt):
                try:
                    # 记录下载前的文件状态
                    original_files = set(
                        f
                        for f in os.listdir(save_dir)
                        if os.path.isfile(os.path.join(save_dir, f))
                    )

                    # download click
                    time.sleep(0.5)
                    download_link = dc._wait_and_highlight(
                        By.XPATH, "//button[contains(.,'公告下载')]"
                    )
                    dc._reliable_click(download_link)
                    dc.logger.info("file start downloading ...")

                    # 监控下载进度
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
                                key=lambda f: os.path.getmtime(
                                    os.path.join(save_dir, f)
                                ),
                            )
                            temp_path = os.path.join(save_dir, newest_file)

                            # 检查文件是否完整（大小稳定）
                            size1 = os.path.getsize(temp_path)
                            time.sleep(random.uniform(0.5, 1.0))
                            size2 = os.path.getsize(temp_path)

                            if size1 == size2 and size1 > 0:
                                download_status = True
                                break

                except Exception as e:
                    dc.logger.error(
                        f"Download attempt {attempt+1} failed with error: {str(e)}"
                    )
                    dc._take_screenshot("download_error")

        except ValueError as e:
            self.logger.warning(f"记录不完整: {str(e)}")
            return False  # 文件已下载但记录未保存
        except Exception as e:
            self.logger.error(f"下载失败: {str(e)}")
            raise
        finally:
            try:
                dc.close()
            except Exception as e:
                self.logger.error(f"关闭浏览器时出错: {str(e)}")
        return download_status

    def save_page(
        self,
        data,
        download_dir="cninfo_file/announcements",
        max_fail=1,
    ):
        """
        保存一页公告数据

        参数:
            data (dict): 公告数据
            download_dir (str): 文件下载目录，默认"cninfo_file/announcements"
            max_fail (int): 最大失败次数，默认1

        返回:
            tuple: (是否成功, 保存的文件数)
        """
        # print("save page function")
        page_save_cnt = 0
        try:
            announcements = data.get("announcements")
            if not announcements:  # 处理null和空列表
                print(f"no data has found")
                return False, page_save_cnt

            # 处理有效数据
            max_fail = int(max_fail) if str(max_fail).isdigit() else 1
            fail_cnt = 0
            # base url
            base_url = "https://www.cninfo.com.cn/new/disclosure/detail?"
            for announcement in announcements:
                if fail_cnt >= max_fail:
                    print("reach maximum failure, break")
                    return False, page_save_cnt
                announcement_id = announcement.get("announcementId")
                # print(announcement_id)

                if not announcement or not announcement_id:
                    print("get no announcement")
                    continue

                # 查重检测
                if self.db.record_exists(announcement_id):
                    # print("annoucement exists")
                    continue

                # download
                is_download = False
                success = False
                # create filename to check if file exists in directory
                secName = announcement.get("secName")
                announcementTitle = announcement.get("announcementTitle")
                check_file_name = f"{secName}：{announcementTitle}.pdf"
                check_file_path = os.path.join(download_dir, check_file_name)
                if os.path.exists(check_file_path):
                    print(f"file exists, load info into db: {check_file_name}")
                    is_download = True
                    success = True

                # create download url
                final_url = f"{base_url}announcementId={announcement_id}"

                # if file not in directory
                if not is_download:
                    success = self.save_file(final_url, download_dir)

                adjunctUrl = announcement.get("adjunctUrl", "")
                try:
                    annoucementTime = adjunctUrl.split("/")[1] if adjunctUrl else ""
                except IndexError:
                    annoucementTime = ""

                record = {
                    "secCode": announcement.get("secCode"),
                    "secName": secName,
                    "announcementId": announcement_id,
                    "announcementTitle": announcementTitle,
                    "downloadUrl": final_url,
                    "pageColumn": announcement.get("pageColumn"),
                    "announcementTime": annoucementTime,
                }
                if success:
                    self.db.save_record(record)
                    page_save_cnt += 1
                else:
                    print("download failed")
                    fail_cnt += 1

            return True, page_save_cnt

        except Exception as e:
            print(f"保存失败: {e}")
            return False, page_save_cnt


def main():
    """
    交互式设计
    """
    announcementDownloader = Cninfo()
    while True:
        print("\n请选择功能：")
        print("A. 根据对应日期查询已下载公告数量")
        print("B. 下载公告")
        print("Q. 退出程序")

        choice = input("请输入选项(A/B/Q): ").upper()

        if choice == "A":
            date = str(input("请输入目标日期(格式:YYYY-MM-DD): "))
            total = announcementDownloader.query_record(date)
            downloaded = announcementDownloader.db.get_count_by_date(date)
            print(f"\n目标日期公告数量: {total}")
            print(f"目标日期已下载公告数量: {downloaded}")

        elif choice == "B":
            print("\n请输入您想要下载的公告日期区间")
            start_date = input("请输入【开始日期】(格式:YYYY-MM-DD): ")
            end_date = input("请输入【结束日期】(格式:YYYY-MM-DD): ")
            print(f"您希望的查询日期区间是: {start_date} ~ {end_date}")

            # select mode
            print("请选择您要使用的下载功能")
            print("a. 基础下载（下载日期区间内所有公告）")
            print("b. 进阶下载（您可根据【公告关键词】【股市板块】筛选公告进行下载）")
            print("e. 返回上一级目录")
            print("q. 退出程序")

            subchoice = input("请输入选项(a / b / e / q): ").lower()

            if subchoice == "a":
                print(f"您希望的查询日期区间是: {start_date} ~ {end_date}")
                confirm = input("请确认开始下载(Y/N): ").upper()
                if confirm == "Y":
                    print("正在为您启动下载...")
                    announcementDownloader.query(start_date, end_date)
                    print("下载完成")
                else:
                    print("返回上一级目录")

            elif subchoice == "b":
                # personalize
                keywords = input("请输入【公告关键词】，若不需要，请输入【NO】: ")
                if keywords == "NO":
                    keywords = "NoSet"

                print(
                    "股市板块有：\nsz：深市 \nszmb：深主板 \nszcy：创业板 \nsh：沪市 \nshmb：沪主板 \nshkcp：科创板 \nbj：北交所"
                )
                plate = input(
                    "请输入【股市板块】对应缩写(sz/szmb/szcy/sh/shmb/shkcp/bj)，若不需要，请输入【NO】: "
                )
                if plate == "NO":
                    plate = "NoSet"

                print(f"\n请确认，您希望的公告下载范围是:")
                print(f"【公告关键词】: {keywords}")
                print(f"【股市板块】: {plate}")
                print(f"您希望的查询日期区间是: {start_date} ~ {end_date}")

                confirm = input("确认下载?【Y/y】确认，【N/n】返回: ").upper()
                if confirm == "Y":
                    print("开始下载...")
                    # 调用进阶下载函数
                    keywords = keywords if keywords != "NoSet" else ""
                    plate = plate if plate != "NoSet" else ""
                    announcementDownloader.edit_payload(keywords, plate)
                    announcementDownloader.query(start_date, end_date)
                    print("下载完成")
                else:
                    print("返回上级目录")
                    continue
            elif subchoice == "q":
                break

            else:
                print("返回上一级目录")

        elif choice == "Q":
            print("程序退出")
            break

        else:
            print("无效选项，请重新选择")


if __name__ == "__main__":
    main()
