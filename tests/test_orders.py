import pytest
from utils.logger import logger
from jsonschema import validate
from utils.schemas import order_schema
class TestOrders:

    # ========== 下单 ==========
    @pytest.mark.regression
    def test_create_order_empty_cart(self, api, registered_user):
        """空购物车下单失败"""
        resp = api.post("/orders")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "购物车为空"

    @pytest.mark.smoke
    def test_create_order_success(self, api, registered_user):
        """正常下单成功"""
        # 创建商品
        api.post("/products", json={"name": "订单商品", "price": 100, "stock": 10})
        products = api.get("/products").json()
        product_id = products[0]["id"]

        # 加入购物车
        api.post("/cart", json={"product_id": product_id, "quantity": 2})

        # 下单
        resp = api.post("/orders")
        assert resp.status_code == 200
        data = resp.json()
        assert "order_id" in data
        assert data["total_amount"] == 200  # 100 * 2
        assert data["status"] == "pending"

    @pytest.mark.regression
    def test_create_order_reduces_stock(self, api, registered_user):
        """下单后库存扣减"""
        # 创建商品，库存 10
        api.post("/products", json={"name": "库存商品", "price": 50, "stock": 10})
        products = api.get("/products").json()
        product_id = products[0]["id"]
        original_stock = products[0]["stock"]

        # 加入购物车，数量 3
        api.post("/cart", json={"product_id": product_id, "quantity": 3})

        # 下单
        api.post("/orders")

        # 验证库存扣减
        products_after = api.get("/products").json()
        product_after = [p for p in products_after if p["id"] == product_id][0]
        assert product_after["stock"] == original_stock - 3  # 10 - 3 = 7

    @pytest.mark.regression
    def test_create_order_insufficient_stock(self, api, registered_user):
        """库存不足下单失败"""
        # 创建商品，库存只有 2
        api.post("/products", json={"name": "缺货商品", "price": 50, "stock": 2})
        products = api.get("/products").json()
        product_id = products[0]["id"]

        # 加入购物车，数量 5（超过库存）
        api.post("/cart", json={"product_id": product_id, "quantity": 5})

        # 下单
        resp = api.post("/orders")
        assert resp.status_code == 400
        assert "库存不足" in resp.json()["detail"]

    @pytest.mark.regression
    def test_create_order_without_login(self, api):
        """未登录下单"""
        resp = api.post("/orders")
        assert resp.status_code == 401

    # ========== 查询订单 ==========
    @pytest.mark.regression
    def test_get_orders_empty(self, api, registered_user):
        """空订单列表"""
        resp = api.get("/orders")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.regression
    def test_get_orders_after_creation(self, api, registered_user):
        """下单后查询订单"""
        # 创建商品并下单
        api.post("/products", json={"name": "查询商品", "price": 30, "stock": 10})
        products = api.get("/products").json()
        product_id = products[0]["id"]
        api.post("/cart", json={"product_id": product_id, "quantity": 1})
        api.post("/orders")

        # 查询订单
        resp = api.get("/orders")
        assert resp.status_code == 200
        orders = resp.json()
        assert len(orders) == 1
        assert orders[0]["total_amount"] == 30
        assert orders[0]["status"] == "pending"
        # Schema 校验每个订单
        for order in orders:
            validate(instance=order, schema=order_schema)

    # ========== 取消订单 ==========

    @pytest.mark.regression
    def test_cancel_order(self, api, registered_user):
        """取消订单成功"""
        # 创建商品并下单
        api.post("/products", json={"name": "取消商品", "price": 40, "stock": 10})
        products = api.get("/products").json()
        product_id = products[0]["id"]
        api.post("/cart", json={"product_id": product_id, "quantity": 2})
        order_resp = api.post("/orders")
        order_id = order_resp.json()["order_id"]

        # 取消订单
        resp = api.post(f"/orders/{order_id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["message"] == "订单已取消"

        # 验证订单状态
        orders = api.get("/orders").json()
        assert orders[0]["status"] == "cancelled"

    @pytest.mark.regression
    def test_cancel_order_restores_stock(self, api, registered_user):
        """取消订单后库存恢复"""
        # 创建商品
        api.post("/products", json={"name": "恢复库存商品", "price": 60, "stock": 10})
        products = api.get("/products").json()
        product_id = products[0]["id"]

        # 加入购物车并下单（数量 4）
        api.post("/cart", json={"product_id": product_id, "quantity": 4})
        order_resp = api.post("/orders")
        order_id = order_resp.json()["order_id"]

        # 此时库存应该是 10 - 4 = 6
        products_after_order = api.get("/products").json()
        stock_after_order = [p for p in products_after_order if p["id"] == product_id][0]["stock"]
        assert stock_after_order == 6

        # 取消订单
        api.post(f"/orders/{order_id}/cancel")

        # 库存应该恢复为 10
        products_after_cancel = api.get("/products").json()
        stock_after_cancel = [p for p in products_after_cancel if p["id"] == product_id][0]["stock"]
        assert stock_after_cancel == 10

    @pytest.mark.regression
    def test_cancel_order_twice(self, api, registered_user):
        """重复取消订单"""
        # 创建商品并下单
        api.post("/products", json={"name": "重复取消商品", "price": 20, "stock": 10})
        products = api.get("/products").json()
        product_id = products[0]["id"]
        api.post("/cart", json={"product_id": product_id, "quantity": 1})
        order_resp = api.post("/orders")
        order_id = order_resp.json()["order_id"]

        # 第一次取消
        api.post(f"/orders/{order_id}/cancel")

        # 第二次取消
        resp = api.post(f"/orders/{order_id}/cancel")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "订单已取消"

    @pytest.mark.regression
    def test_cancel_nonexistent_order(self, api, registered_user):
        """取消不存在的订单"""
        resp = api.post("/orders/99999/cancel")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "订单不存在"