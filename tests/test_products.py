import pytest
from utils.logger import logger
from jsonschema import validate
from utils.schemas import product_schema
from utils.data_loader import load_json
import os

# 加载商品测试数据
PRODUCTS_DATA = load_json(
    os.path.join("config", "test_data", "products.json")
)
class TestProducts:

    # ========== 创建商品 ==========
    @pytest.mark.smoke
    def test_create_product_success(self, api, registered_user):
        """创建商品成功"""
        resp = api.post("/products", json={
            "name": "测试商品",
            "price": 99.9,
            "stock": 10
        })
        assert resp.status_code == 200
        assert resp.json()["message"] == "商品创建成功"

    @pytest.mark.parametrize("product", PRODUCTS_DATA["invalid_prices"])
    @pytest.mark.regression
    def test_create_product_invalid_price(self, api, registered_user, product):
        """价格非法创建失败（数据驱动）"""
        resp = api.post("/products", json=product)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "价格必须大于 0"

    @pytest.mark.parametrize("product", PRODUCTS_DATA["invalid_stocks"])
    @pytest.mark.regression
    def test_create_product_invalid_stock(self, api, registered_user, product):
        """库存非法创建失败（数据驱动）"""
        resp = api.post("/products", json=product)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "库存不能为负"

    @pytest.mark.regression
    def test_create_product_without_login(self, api):
        """未登录创建商品失败"""
        resp = api.post("/products", json={
            "name": "未登录商品",
            "price": 50,
            "stock": 10
        })
        assert resp.status_code == 401

    # ========== 查询商品 ==========
    @pytest.mark.smoke
    def test_get_product_list(self, api, registered_user):
        """获取商品列表"""
        # 先创建两个商品
        api.post("/products", json={"name": "商品A", "price": 10, "stock": 5})
        api.post("/products", json={"name": "商品B", "price": 20, "stock": 8})

        resp = api.get("/products")
        assert resp.status_code == 200
        products = resp.json()
        assert isinstance(products, list)
        assert len(products) == 2
        # Schema 校验列表中每个商品
        for product in products:
            validate(instance=product, schema=product_schema)

    @pytest.mark.regression
    def test_get_single_product(self, api, registered_user):
        """查询单个商品"""
        # 创建商品
        api.post("/products", json={"name": "单品", "price": 30, "stock": 3})

        # 获取列表拿到 ID
        products = api.get("/products").json()
        product_id = products[0]["id"]

        resp = api.get(f"/products/{product_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == product_id
        assert data["name"] == "单品"
        assert data["price"] == 30
        assert data["stock"] == 3
        # Schema 校验
        validate(instance=data, schema=product_schema)

    @pytest.mark.regression
    def test_get_nonexistent_product(self, api, registered_user):
        """查询不存在的商品"""
        resp = api.get("/products/99999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "商品不存在"

    # ========== 更新商品 ==========

    @pytest.mark.regression
    def test_update_product(self, api, registered_user):
        """更新商品成功"""
        # 创建
        api.post("/products", json={"name": "原商品", "price": 10, "stock": 5})
        products = api.get("/products").json()
        product_id = products[0]["id"]

        # 更新
        resp = api.put(f"/products/{product_id}", json={
            "name": "新商品",
            "price": 99,
            "stock": 20
        })
        assert resp.status_code == 200

        # 验证更新结果
        get_resp = api.get(f"/products/{product_id}")
        data = get_resp.json()
        assert data["name"] == "新商品"
        assert data["price"] == 99
        assert data["stock"] == 20

    @pytest.mark.regression
    def test_update_nonexistent_product(self, api, registered_user):
        """更新不存在的商品"""
        resp = api.put("/products/99999", json={
            "name": "不存在",
            "price": 1,
            "stock": 1
        })
        assert resp.status_code == 404
        assert resp.json()["detail"] == "商品不存在"

    # ========== 删除商品 ==========

    @pytest.mark.regression
    def test_delete_product(self, api, registered_user):
        """删除商品成功"""
        # 创建
        api.post("/products", json={"name": "待删商品", "price": 10, "stock": 5})
        products = api.get("/products").json()
        product_id = products[0]["id"]

        # 删除
        resp = api.delete(f"/products/{product_id}")
        assert resp.status_code == 200

        # 验证已删除
        get_resp = api.get(f"/products/{product_id}")
        assert get_resp.status_code == 404

    @pytest.mark.regression
    def test_delete_nonexistent_product(self, api, registered_user):
        """删除不存在的商品"""
        resp = api.delete("/products/99999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "商品不存在"

    @pytest.mark.regression
    def test_create_product_missing_name(self, api, registered_user):
        """创建商品缺少 name 字段"""
        resp = api.post("/products", json={
            "price": 50,
            "stock": 10
        })
        assert resp.status_code == 422

    @pytest.mark.regression
    def test_get_product_invalid_id(self, api, registered_user):
        """查询商品传入非数字 ID"""
        resp = api.get("/products/abc")
        assert resp.status_code == 422

    @pytest.mark.regression
    def test_access_with_invalid_token(self, api):
        """使用无效 token 访问"""
        api.set_token("invalid_token_123")
        resp = api.get("/cart")
        assert resp.status_code == 401