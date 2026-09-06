import json
import os

def load_json(file_path):
    """加载 JSON 文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_test_data(file_name):
    """从 test_data 目录加载测试数据"""
    base_path = os.path.join("config", "test_data")
    file_path = os.path.join(base_path, file_name)
    return load_json(file_path)