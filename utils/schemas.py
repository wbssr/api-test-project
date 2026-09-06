# 商品 Schema
product_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "price": {"type": "number"},
        "stock": {"type": "integer"},
        "created_at": {"type": "string"}
    },
    "required": ["id", "name", "price", "stock"]
}

# 购物车项 Schema
cart_item_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "product_id": {"type": "integer"},
        "quantity": {"type": "integer"},
        "name": {"type": "string"},
        "price": {"type": "number"}
    },
    "required": ["id", "product_id", "quantity", "name", "price"]
}

# 订单 Schema
order_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "user_id": {"type": "integer"},
        "total_amount": {"type": "number"},
        "status": {"type": "string"},
        "created_at": {"type": "string"}
    },
    "required": ["id", "user_id", "total_amount", "status"]
}