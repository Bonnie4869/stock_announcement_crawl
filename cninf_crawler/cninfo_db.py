import sqlite3
from typing import Dict
import os
import logging


class CninfoAnnouncementDB:
    def __init__(self, db_path: str):
        """
        初始化公告数据库
        参数:
            db_path: 数据库文件路径
        """
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = os.path.abspath(db_path)
        self.logger = logging.getLogger("CninfoAnnouncementDB")
        self._init_db()
        self._id_cache = set()
        self._load_id_cache()

    def _init_db(self):
        """
        初始化数据库表结构
        表结构:
            - secCode: 股票代码
            - secName: 股票名称
            - announcementId: 公告ID(主键)
            - announcementTitle: 公告标题
            - downloadUrl: 公告URL
            - pageColumn: 页面栏目
            - announcementTime: 公告时间
        """
        with self._get_connection() as conn:
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS announcements (
                secCode TEXT NOT NULL,
                secName TEXT NOT NULL,
                announcementId TEXT PRIMARY KEY,
                announcementTitle TEXT NOT NULL,
                downloadUrl TEXT NOT NULL,
                pageColumn TEXT,
                announcementTime TEXT
            )"""
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_secCode ON announcements(secCode)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_announcementId ON announcements(announcementId)"
            )

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_id_cache(self):
        """加载现有公告ID到内存缓存"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT announcementId FROM announcements")
            self._id_cache = {row["announcementId"] for row in cursor.fetchall()}

    def record_exists(self, announcement_id: str) -> bool:
        """
        检查公告是否已存在
        参数:
            announcement_id: 公告ID
        返回:
            bool: 是否存在
        """
        return announcement_id in self._id_cache

    def save_record(self, record: Dict) -> bool:
        """
        保存公告记录到数据库
        参数:
            record: 公告字典，必须包含以下字段:
                - secCode: 股票代码
                - secName: 股票名称
                - announcementId: 公告ID
                - announcementTitle: 公告标题
                - downloadUrl: 公告URL
                - pageColumn: 页面栏目
                - announcementTime: 公告时间
        返回:
            bool: 是否保存成功
        """
        required_fields = [
            "secCode",
            "secName",
            "announcementId",
            "announcementTitle",
            "downloadUrl",
            "pageColumn",
        ]
        if not all(field in record for field in required_fields):
            self.logger.error("缺少必要字段")
            return False

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                INSERT OR REPLACE INTO announcements (
                    secCode, secName, announcementId, 
                    announcementTitle, downloadUrl, pageColumn, announcementTime
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        record["secCode"],
                        record["secName"],
                        record["announcementId"],
                        record["announcementTitle"],
                        record["downloadUrl"],
                        record["pageColumn"],
                        record["announcementTime"],
                    ),
                )
                self._id_cache.add(record["announcementId"])
                return True
        except Exception as e:
            self.logger.error(f"保存失败: {str(e)}")
            return False

    def get_all_records(self) -> list:
        """获取所有公告记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM announcements")
            return [dict(row) for row in cursor.fetchall()]

    def delete_record(self, announcement_id: str) -> bool:
        """
        删除指定公告
        参数:
            announcement_id: 要删除的公告ID
        返回:
            bool: 是否删除成功
        """
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "DELETE FROM announcements WHERE announcementId = ?",
                    (announcement_id,),
                )
                if announcement_id in self._id_cache:
                    self._id_cache.remove(announcement_id)
                return True
        except Exception as e:
            self.logger.error(f"删除失败: {str(e)}")
            return False

    def get_records_by_date(self, date: str) -> list:
        """
        获取指定日期的公告记录
        参数:
            date: 查询日期 (格式: 'YYYY-MM-DD')
        返回:
            list: 当天的公告记录列表，按时间排序（如果需要）
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM announcements WHERE date(announcementTime) = ?", (date,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_count_by_date(self, date: str) -> int:
        """
        获取指定日期的公告数量
        参数:
            date: 查询日期 (格式: 'YYYY-MM-DD')
        返回:
            int: 当天的公告数量
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM announcements WHERE date(announcementTime) = ?",
                (date,),
            )
            return cursor.fetchone()[0]
