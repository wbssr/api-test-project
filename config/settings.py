import os

class Settings:
    # 被测系统地址
    BASE_URL = "http://localhost:8000"

    # 测试账号（测试时动态注册）
    TEST_USER_EMAIL = "test_user@example.com"
    TEST_USER_PASSWORD = "123456"
    TEST_USER_NAME = "测试用户"

    # 数据库文件路径（测试库）
    DB_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "test_api.db"
    )
settings = Settings()