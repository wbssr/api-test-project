一键复制 README.md
markdown
# 电商系统接口自动化测试框架

## 项目简介

基于 FastAPI 自建的电商后端系统 + pytest 接口自动化测试框架。

被测系统包含认证、商品、购物车、订单 4 个模块，共 15 个 REST API。
测试框架覆盖正向流程、异常场景、边界条件、接口关联和业务逻辑校验。

## 技术栈

| 模块 | 技术 |
| :--- | :--- |
| 被测系统 | FastAPI + SQLite |
| 测试框架 | pytest + requests |
| 数据驱动 | JSON 文件 |
| 响应校验 | JSON Schema |
| 测试分级 | pytest mark（smoke / regression） |
| 日志 | logging |
| 测试报告 | Allure |

## 项目结构
```
api-test-project/
├── app.py                    # 被测系统（FastAPI）
├── config/
│   ├── __init__.py
│   ├── settings.py           # 全局配置
│   └── test_data/            # 测试数据（JSON）
│       ├── products.json     # 商品测试数据
│       └── users.json        # 用户测试数据
├── utils/
│   ├── __init__.py
│   ├── api_client.py         # API 客户端封装
│   ├── logger.py             # 日志模块
│   ├── data_loader.py        # 数据加载
│   └── schemas.py            # JSON Schema 定义
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # fixture 管理
│   ├── test_auth.py          # 认证模块测试
│   ├── test_products.py      # 商品模块测试
│   ├── test_cart.py          # 购物车模块测试
│   └── test_orders.py        # 订单模块测试
├── requirements.txt
├── pytest.ini
└── README.md
```


## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动被测系统
```bash
uvicorn app:app --reload --port 8000
```
### 3. 运行测试
```bash
# 全部测试
pytest tests/ -v

# 冒烟测试
pytest tests/ -m smoke -v

# 回归测试
pytest tests/ -m regression -v

# 生成 Allure 报告
pytest tests/ -v --alluredir=reports/allure-results
allure serve reports/allure-results
```
### 测试覆盖
| 模块 | 用例数 | 覆盖内容 |
| :--- | :--- | :--- |
| 认证 | 7 | 注册、登录、参数校验、异常场景 |
| 商品 | 14 | CRUD、边界值、权限校验、Schema |
| 购物车 | 9 | 添加、查询、移除、异常场景 |
| 订单 | 11 | 下单、库存扣减、取消、业务逻辑 |
| 总计 | 42 | |
### 核心特性
- 数据驱动：测试数据与代码分离，修改 JSON 即可扩展用例

- Schema 校验：使用 JSON Schema 校验响应结构

- 测试分级：pytest mark 区分冒烟和回归用例

- 数据清理：每个用例前自动清空数据库，保证可重复执行

- 接口关联：覆盖 登录→创建→加购→下单→取消 完整链路

- 日志：每个请求路径和状态码都被记录

### 缺陷发现记录
在补充异常用例时，发现 GET /products 接口未做认证，已通过测试覆盖该场景并确认修复方案。

### 作者
luoqing