import requests
from utils.logger import logger
from config.settings import settings

class ApiClient:
    """API 封装类，所有测试通过它发请求"""

    def __init__(self):
        self.base_url = settings.BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None

    def set_token(self, token):
        """设置认证 token"""
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info("token 已设置")

    def clear_token(self):
        """清除 token"""
        self.token = None
        self.session.headers.pop("Authorization", None)
        logger.info("token 已清除")

    def get(self, path, **kwargs):
        url = f"{self.base_url}{path}"
        logger.info(f"GET {url}")
        resp = self.session.get(url, **kwargs)
        logger.info(f"响应状态码: {resp.status_code}")
        return resp

    def post(self, path, **kwargs):
        url = f"{self.base_url}{path}"
        logger.info(f"POST {url}")
        resp = self.session.post(url, **kwargs)
        logger.info(f"响应状态码: {resp.status_code}")
        return resp

    def put(self, path, **kwargs):
        url = f"{self.base_url}{path}"
        logger.info(f"PUT {url}")
        resp = self.session.put(url, **kwargs)
        logger.info(f"响应状态码: {resp.status_code}")
        return resp

    def delete(self, path, **kwargs):
        url = f"{self.base_url}{path}"
        logger.info(f"DELETE {url}")
        resp = self.session.delete(url, **kwargs)
        logger.info(f"响应状态码: {resp.status_code}")
        return resp

    def clean_db(self, table_name):
        """清空指定表"""
        import sqlite3
        from config.settings import settings
        conn = sqlite3.connect(settings.DB_PATH)
        conn.execute(f"DELETE FROM {table_name}")
        conn.commit()
        conn.close()
        logger.info(f"已清空表: {table_name}")