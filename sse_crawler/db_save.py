import sqlite3
from typing import Dict, Optional
import os
import logging
from datetime import datetime
import hashlib


class AnnouncementDB:
    def __init__(self, db_path: str):
        """
        输入:
          db_path: 数据库文件路径(see：data/announcements.db)
        输出: 无
        功能:
          1. 创建数据库目录(如果不存在)
          2. 初始化数据库连接
          3. 创建内存中的URL缓存(用于快速去重)
        """
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = os.path.abspath(db_path)
        self.logger = logging.getLogger("AnnouncementDB")
        self._init_db()
        self._url_cache = set()
        self._load_url_cache()

    def _init_db(self):
        """
        初始化数据库表结构
        输入: 无
        输出: 无
        功能:
          1. 创建announcements表(如果不存在)
          2. 建立url_hash和stock_code索引
        表结构:
          - id: 自增主键
          - stock_code: 股票代码
          - stock_name: 股票名称
          - announcement_title: 公告标题
          - announcement_type: 公告类型(可以为空)
          - announcement_date: 公告日期
          - announcement_url: 公告URL(唯一)
          - url_hash: 存储URL的SHA256哈希值（截取前32位/64位）(唯一)
          - file_path: 文件存储路径
          - file_name: 文件名
          - created_time: 记录创建时间
        """
        with self._get_connection() as conn:
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT NOT NULL,
                announcement_title TEXT NOT NULL,
                announcement_type TEXT,
                announcement_date TEXT NOT NULL,
                announcement_url TEXT NOT NULL UNIQUE,
                url_hash TEXT NOT NULL UNIQUE,
                file_path TEXT,
                file_name TEXT,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_url_hash ON announcements(url_hash)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_stock_code ON announcements(stock_code)"
            )  # 修改这里

    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接
        输入: 无
        输出: 返回 sqlite3.Connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _hash_url(self, url: str) -> str:
        """
        生成URL哈希值(SHA256截取前32位)，节省性能，很少有不同的url出现相同的哈希值
        输入: url字符串
        输出: 32位十六进制哈希字符串
        功能: 用于URL唯一性校验
        """
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]

    def _load_url_cache(self):
        """
        加载现有URL哈希到内存缓存
        输入: 无
        输出: 无
        功能: 初始化时预加载所有已有URL的哈希值
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT url_hash FROM announcements")
            self._url_cache = {row["url_hash"] for row in cursor.fetchall()}

    def record_exists(self, url: str) -> bool:
        """
        检查URL是否已存在
        输入: 公告URL
        输出: bool(True表示url已存在于db中)
        功能: 通过cache快速判断url是否重复
        """
        url_hash = self._hash_url(url)
        return url_hash in self._url_cache

    def save_record(self, record: Dict, file_info: Optional[Dict] = None) -> bool:
        """
        保存公告记录到数据库
        输入:
          - record: 公告字典
          - file_info: 文件信息字典
        输出: bool(保存成功返回True)
        功能:
          1. 校验必填字段
          2. 生成URL的哈希值
          3. 执行插入或更新操作
          4. 更新cache
        """
        required_fields = [
            "stock_code",
            "stock_name",
            "announcement_title",
            "announcement_date",
            "announcement_url",
        ]
        if not all(field in record for field in required_fields):
            self.logger.error("lack of essential attribute")
            return False

        url_hash = self._hash_url(record["announcement_url"])
        data = {
            "stock_code": record["stock_code"],
            "stock_name": record["stock_name"],
            "announcement_title": record["announcement_title"],
            "announcement_type": record.get("announcement_type"),
            "announcement_date": record["announcement_date"],
            "announcement_url": record["announcement_url"],
            "url_hash": url_hash,
        }

        if file_info:
            data.update(
                {
                    "file_name": file_info.get("file_name"),
                    "file_path": file_info.get("file_path"),
                }
            )

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                INSERT INTO announcements (
                    stock_code, stock_name, announcement_title, announcement_type, announcement_date, 
                    announcement_url, url_hash, file_name, file_path
                ) VALUES (
                    :stock_code, :stock_name, :announcement_title, :announcement_type, :announcement_date,
                    :announcement_url, :url_hash, :file_name, :file_path
                )
                ON CONFLICT(announcement_url) DO UPDATE SET
                    file_name = excluded.file_name,
                    file_path = excluded.file_path
                """,
                    data,
                )
                self._url_cache.add(url_hash)
                return True
        except Exception as e:
            self.logger.error(f"save failed: {str(e)}")
            return False
