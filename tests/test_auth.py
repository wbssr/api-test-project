import pytest
from utils.logger import logger
from utils.data_loader import load_json
import os

USERS_DATA = load_json(os.path.join("config", "test_data", "users.json"))
class TestAuth:
    @pytest.mark.smoke
    def test_register_success(self, api, clean_db):
        """注册成功"""
        clean_db()

        resp = api.post("/register", json={
            "email": "new_user@example.com",
            "password": "123456",
            "name": "新用户"
        })
        assert resp.status_code == 200
        assert resp.json()["message"] == "注册成功"
    @pytest.mark.regression
    def test_register_duplicate_email(self, api, registered_user):
        """重复注册"""
        resp = api.post("/register", json={
            "email": registered_user["email"],
            "password": "123456",
            "name": "重复用户"
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == "该邮箱已注册"

    @pytest.mark.parametrize("user", USERS_DATA["invalid_registrations"])
    @pytest.mark.regression
    def test_register_invalid(self, api, user):
        """非法注册失败（数据驱动）"""
        resp = api.post("/register", json={
            "email": user["email"],
            "password": user["password"],
            "name": user["name"]
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == user["expected_detail"]

    @pytest.mark.smoke
    def test_login_success(self, registered_user):
        """登录成功"""
        assert "token" in registered_user
        assert registered_user["name"] == "测试用户"

    @pytest.mark.regression
    def test_login_wrong_password(self, api, registered_user):
        """密码错误"""
        resp = api.post("/login", json={
            "email": registered_user["email"],
            "password": "wrong_password"
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "邮箱或密码错误"

    @pytest.mark.regression
    def test_login_missing_password(self, api, registered_user):
        """登录缺少密码字段"""
        resp = api.post("/login", json={
            "email": registered_user["email"]
        })
        assert resp.status_code == 422

    @pytest.mark.regression
    def test_register_missing_name(self, api):
        """注册缺少 name 字段"""
        resp = api.post("/register", json={
            "email": "no_name@example.com",
            "password": "123456"
        })
        assert resp.status_code == 422