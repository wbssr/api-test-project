import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from utils.api_client import ApiClient
from utils.logger import logger
from config.settings import settings

@pytest.fixture(scope="function")
def api():
    """每个测试用例独立的 API 客户端"""
    client = ApiClient()
    yield client
    client.clear_token()

@pytest.fixture(scope="function")
def clean_db():
    """测试前清空所有业务表，保证环境干净"""
    def _clean():
        api = ApiClient()
        for table in ["order_items", "orders", "carts", "products", "tokens", "users"]:
            api.clean_db(table)
        logger.info("测试数据库已清空")
    return _clean

@pytest.fixture(scope="function")
def registered_user(api, clean_db):
    """注册并登录一个测试用户，返回用户信息"""
    clean_db()  # 先清空

    email = "test_user@example.com"
    password = "123456"
    name = "测试用户"

    # 注册
    resp = api.post("/register", json={
        "email": email,
        "password": password,
        "name": name
    })
    assert resp.status_code == 200

    # 登录
    login_resp = api.post("/login", json={
        "email": email,
        "password": password
    })
    assert login_resp.status_code == 200

    token = login_resp.json()["token"]
    api.set_token(token)

    return {
        "email": email,
        "password": password,
        "name": name,
        "token": token
    }