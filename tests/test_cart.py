import pytest
from utils.logger import logger
from jsonschema import validate
from utils.schemas import cart_item_schema
class TestCart:

    # ========== 添加购物车 ==========
    @pytest.mark.smoke
    def test_add_to_cart_success(self, api, registered_user):
        """添加商品到购物车成功"""
        # 先创建商品
        api.post("/products", json={"name": "购物车商品", "price": 50, "stock": 20})
        products = api.get("/products").json()
        product_id = products[0]["id"]

        # 加入购物车
        resp = api.post("/cart", json={
            "product_id": product_id,
            "quantity": 2
        })
        assert resp.status_code == 200
        assert resp.json()["message"] == "已加入购物车"

        # 验证购物车里有商品
        cart_resp = api.get("/cart")
        cart_items = cart_resp.json()
        assert len(cart_items) == 1
        assert cart_items[0]["product_id"] == product_id
        assert cart_items[0]["quantity"] == 2

    @pytest.mark.regression
    def test_add_nonexistent_product(self, api, registered_user):
        """添加不存在的商品"""
        resp = api.post("/cart", json={
            "product_id": 99999,
            "quantity": 1
        })
        assert resp.status_code == 404
        assert resp.json()["detail"] == "商品不存在"

    @pytest.mark.regression
    def test_add_zero_quantity(self, api, registered_user):
        """数量为 0"""
        api.post("/products", json={"name": "零数量商品", "price": 50, "stock": 20})
        products = api.get("/products").json()
        product_id = products[0]["id"]

        resp = api.post("/cart", json={
            "product_id": product_id,
            "quantity": 0
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == "数量必须大于 0"

    @pytest.mark.regression
    def test_add_negative_quantity(self, api, registered_user):
        """数量为负"""
        api.post("/products", json={"name": "负数量商品", "price": 50, "stock": 20})
        products = api.get("/products").json()
        product_id = products[0]["id"]

        resp = api.post("/cart", json={
            "product_id": product_id,
            "quantity": -3
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == "数量必须大于 0"

    @pytest.mark.regression
    def test_add_without_login(self, api):
        """未登录添加购物车"""
        resp = api.post("/cart", json={
            "product_id": 1,
            "quantity": 1
        })
        assert resp.status_code == 401

    # ========== 查看购物车 ==========

    @pytest.mark.regression
    def test_get_empty_cart(self, api, registered_user):
        """空购物车"""
        resp = api.get("/cart")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.regression
    def test_get_cart_with_items(self, api, registered_user):
        """有商品的购物车"""
        # 创建两个商品
        api.post("/products", json={"name": "商品1", "price": 10, "stock": 20})
        api.post("/products", json={"name": "商品2", "price": 20, "stock": 20})
        products = api.get("/products").json()

        # 两个都加入购物车
        api.post("/cart", json={"product_id": products[0]["id"], "quantity": 1})
        api.post("/cart", json={"product_id": products[1]["id"], "quantity": 3})

        resp = api.get("/cart")
        items = resp.json()
        assert len(items) == 2
        # Schema 校验每个购物车项
        for item in items:
            validate(instance=item, schema=cart_item_schema)

        # 验证每个字段
        for item in items:
            assert "id" in item
            assert "product_id" in item
            assert "quantity" in item
            assert "name" in item
            assert "price" in item

    # ========== 移除购物车 ==========

    @pytest.mark.regression
    def test_remove_from_cart(self, api, registered_user):
        """移除购物车项"""
        api.post("/products", json={"name": "待移除商品", "price": 10, "stock": 10})
        products = api.get("/products").json()
        product_id = products[0]["id"]

        api.post("/cart", json={"product_id": product_id, "quantity": 1})
        cart_items = api.get("/cart").json()
        cart_id = cart_items[0]["id"]

        resp = api.delete(f"/cart/{cart_id}")
        assert resp.status_code == 200

        # 验证已移除
        cart_resp = api.get("/cart")
        assert cart_resp.json() == []

    @pytest.mark.regression
    def test_remove_nonexistent_cart_item(self, api, registered_user):
        """移除不存在的购物车项"""
        resp = api.delete("/cart/99999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "购物车项不存在"